import logging
import pandas as pd
from extract import extract
from mappings import Mappings
from gen_journal_line import GenJournalLine


def extract_raw_data():
    raw = extract()
    return raw['ledger_header'], raw['ledger_details'], raw['amazon_transactions']


def prepare_amazon(am_df):
    logging.info("Preparing AM data")

    am_df = am_df.copy()

    # Map am transaction types to document types: gl-acc, invoices and credit memos
    am_df["type_map"] = am_df["Transaction type"].map(Mappings.AM_PMT).fillna("gl_acc")
    am_df["Date"] = pd.to_datetime(am_df["Date"], errors="coerce")

    # Create merge keys: order id and document type
    am_df["key"] = (am_df["Order ID"] + "_" + am_df["type_map"].str.lower()).str.strip()

    logging.info("AM data complete")
    return am_df.add_prefix("am_")


def prepare_cle(cle_df, dcle_df):
    logging.info(
    "Preparing ERP data: CLE (%d rows), DCLE (%d rows)",
    len(cle_df), len(dcle_df)
    )


    cle_df = cle_df.copy()
    dcle_df = dcle_df.copy()

    # cle_df.columns = [col.replace(" ", "_").lower() for col in cle_df.columns]
    # dcle_df.columns = [col.replace(" ", "_").lower() for col in dcle_df.columns]
    
    # Create merge keys: external document no. and document type
    cle_df["key"] = (cle_df["External Document No_"] + "_" + cle_df["Document Type"].str.lower()).str.strip()

    # Calculate reconciliation amount
    cle_df["ocf_amount"] = cle_df["Sales (LCY)"] * cle_df["Original Currency Factor"]

    cle_df = cle_df.add_prefix("cle_")
    dcle_df = dcle_df.add_prefix("dcle_")

    # Merge customer ledger entries and detailed customer ledger entries
    merged = pd.merge(
        cle_df,
        dcle_df,
        how="left",
        left_on="cle_Entry No_",
        right_on="dcle_Cust_ Ledger Entry No_",
        indicator="le_merge"
    )

    logging.info("Ledger merge complete: %d rows", len(merged))
    return merged


def merge_amazon_cle(am, cle):
    logging.info("Merging Amazon (%d rows) with CLE (%d rows)", len(am), len(cle))

    # Merge amazon transactions with erp customer ledger entries
    data = pd.merge(
        am,
        cle,
        how="left",
        left_on="am_key",
        right_on="cle_key",
        indicator=True
    )

    # Dublicate fields for reorder columns
    data["am_Amazon_fees"] = data["am_Amazon fees"]
    data["am_Total_(EUR)"] = data["am_Total (EUR)"]

    data["am_amount_ex_fee"] = round(
        data["am_Total product charges"] +
        data["am_Total promotional rebates"] +
        data["am_Other"], 2
    )
    # Reconcile amounts in currency (not LCY)
    # data["dcle_amount"] = round(data["dcle_Amount"], 2)
    data["recon_amount"] = round(data["am_amount_ex_fee"] - data["dcle_Amount"])

    # cols_to_move = ["am_amount_ex_fee", "dcle_amount", "recon_amount"]
    cols_to_move = ["am_amount_ex_fee", "recon_amount"]
    data = data[[c for c in data.columns if c not in cols_to_move] + cols_to_move]

    logging.info("Merge complete: %d rows in merged dataset", len(data))
    return data


def melt_amounts(data):
    logging.info("Melting amount columns (%d rows before melt)", len(data))

    # Create journal lines for each posting amount by melting columns
    value_vars = ["am_amount_ex_fee", "am_Amazon_fees", "am_Total_(EUR)"] 
    melted = data.melt(
        id_vars=[c for c in data.columns if c not in value_vars],
        value_vars=value_vars,
        var_name="amount_posting_type",
        value_name="Amount"
    )

    # Flag G/L Account expenses 
    gl_types = ["Commingling VAT", "Order retrocharge", "Other", "Service Fees"]
    melted = melted[
        ~(
            melted["am_Transaction type"].isin(gl_types)
            & (melted["amount_posting_type"] != "am_Total_(EUR)")
        )
    ]

    # # Rename lines flagged as GL expenses 
    # melted.loc[melted["am_type_map"] == "gl_acc", "amount_posting_type"] = (
    #     melted["am_type_map"] + "_" + melted["amount_posting_type"]
    # )

    melted["amount_posting_type"] = (
        melted["am_type_map"] + "_" + melted["amount_posting_type"]
    )

    # Rename and create values for posting description in journal 
    melted["posting_description"] = (
        melted["am_Transaction type"] + " " +
        melted["amount_posting_type"].replace(Mappings.RENAME)
    )

    logging.info("Melt complete (%d rows after melt)", len(melted))
    return melted.sort_values(by=["am_Date", "am_Order ID"]).reset_index(drop=True)


def transactions_match(am_df, cle_df, dcle_df):
    logging.info("Starting transactions match")

    # Prepare data
    am = prepare_amazon(am_df)
    cle = prepare_cle(cle_df, dcle_df)

    # Match Amazon payments to erp customer ledger entries by merging payments to invoices and credit memos 
    merged = merge_amazon_cle(am, cle)
    melted = melt_amounts(merged)

    logging.info("Transactions match complete")
    return melted


def split_flagged(data):
    # Flagged for manuel entry if no invoice or credit memo in ERP
    # If there is a document match there is a customer number to post payment
    # If document is open, then apply payment to invoice
    # If document is closed, post payment but do not apply
    flagged = (
        ((data["am_type_map"] == "invoice") |
         (data["am_type_map"] == "credit memo")) &
        (~data["am_key"].isin(data["cle_key"]))
    )
    
    return data[~flagged].copy(), data[flagged].copy()


def create_gen_journal(data):

    # Create erp posting journal using the general journal line class  
    journal = []
    for index, row in data.iterrows():
        # create journal line number
        Line_no = (index + 1) * 10000

        # Determine erp posting type by payment type lookup in mapping
        posting_type = Mappings.PMT_SETUP[row["amount_posting_type"]]
        line = GenJournalLine.create_gen_journal_line(Line_no, row, posting_type)

        journal.append(line)

    return journal


def build_journals(data_import, data_flagged):
    logging.info("Building journal lines for import journal lines")
    journal_import = pd.DataFrame(create_gen_journal(data_import))

    logging.info("Building journal lines for flagged journal lines")
    journal_flagged = pd.DataFrame(create_gen_journal(data_flagged))

    return journal_import, journal_flagged


def mask_fields(dataframe):
    data_mask = dataframe.copy()

    mask_value = "*" * 10 
    for col in Mappings.mask_cols:
        if col in data_mask.columns:
            data_mask[col] = mask_value

    return data_mask


def transform():
    logging.info("Starting data transformation")

    # 1. Extract data
    cle_df, dcle_df, am_df = extract_raw_data()

    logging.info(
    "Extracted datasets: ledger_header=%d, ledger_details=%d, amazon_transactions=%d",
    len(cle_df), len(dcle_df), len(am_df))


    # 2. Perform transaction reconciliation
    data = transactions_match(am_df, cle_df, dcle_df)

    logging.info("Transaction match complete: %d rows", len(data))


    # 3. Split valid and flagged payments - no invoice or credit memo in ERP
    logging.info("Splitting matched data into normal and flagged sets")
    data_import, data_flagged = split_flagged(data)

    logging.info("Normal journal lines: %d | Flagged journal lines: %d", len(data_import), len(data_flagged))


    # 4. Build journals
    logging.info("Building journal lines")
    journal_import, journal_flagged = build_journals(data_import, data_flagged)

    logging.info("Journals creation complete")
    

    # 5. Mask data
    logging.info("Masking output data")
    data_masked = mask_fields(data)
    journal_import_masked = mask_fields(journal_import)
    journal_flagged_masked = mask_fields(journal_flagged)
    

    logging.info("Masking data Completed")

    # 6 Prepare load
    load_dfs = {
        "output": {
            "data": data,
            "journal_import": journal_import,
            "journal_flagged": journal_flagged
        },
        "output_masked": {
            "data_masked": data_masked,
            "journal_import_masked": journal_import_masked,
            "journal_flagged_masked": journal_flagged_masked
        }
    }

    logging.info("Data transformation complete")
    return load_dfs