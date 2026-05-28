from gen_journal_line import GenJournalDocumentType, GenJournalAccountType, GenJournalLine

class Mappings:
    AM_PMT = {
        "Commingling VAT": "gl_acc",
        "Order Payment": "invoice",
        "Order retrocharge": "gl_acc",
        "Other": "gl_acc",
        "Refund": "credit memo",
        "Service Fees": "gl_acc"
    }

    PMT_SETUP = {
        # Invoice posting
        "invoice_am_amount_ex_fee": {
            "Document Type": GenJournalDocumentType.PAYMENT,
            "Document No.": "",
            "Account Type": GenJournalAccountType.CUSTOMER,
            "Account No.": lambda row: row["cle_Customer No_"],
            "Applies-to Doc. Type": GenJournalDocumentType.INVOICE,
            "Applies-to Doc. No.": lambda row: row["cle_Document No_"],
            "Bal. Account Type": "",
            "Bal. Account No.": "",
            "Signed": -1,
        },

        "invoice_am_Amazon_fees": {
            "Document Type": GenJournalDocumentType.PAYMENT,
            "Document No.": "",
            "Account Type": GenJournalAccountType.GL_ACCOUNT,
            "Account No.": "GL2555",
            "Applies-to Doc. Type": GenJournalDocumentType.BLANK,
            "Applies-to Doc. No.": "",
            "Bal. Account Type": "",
            "Bal. Account No.": "",
            "Signed": -1,
        },

        "invoice_am_Total_(EUR)": {
            "Document Type": GenJournalDocumentType.PAYMENT,
            "Document No.": "",
            "Account Type": GenJournalAccountType.BANK_ACCOUNT,
            "Account No.": "",
            "Applies-to Doc. Type": GenJournalDocumentType.BLANK,
            "Applies-to Doc. No.": "",
            "Bal. Account Type": "",
            "Bal. Account No.": "",
            "Signed": 1,
        },

        # Credit Memo posting
        "credit memo_am_amount_ex_fee": {
            "Document Type": GenJournalDocumentType.PAYMENT,
            "Document No.": "",
            "Account Type": GenJournalAccountType.CUSTOMER,
            "Account No.": lambda row: row["cle_Customer No_"],
            "Applies-to Doc. Type": GenJournalDocumentType.CREDIT_MEMO,
            "Applies-to Doc. No.": lambda row: row["cle_Document No_"],
            "Bal. Account Type": "",
            "Bal. Account No.": "",
            "Signed": -1,
        },

        "credit memo_am_Amazon_fees": {
            "Document Type": GenJournalDocumentType.PAYMENT,
            "Document No.": "",
            "Account Type": GenJournalAccountType.GL_ACCOUNT,
            "Account No.": "GL2555",
            "Applies-to Doc. Type": GenJournalDocumentType.BLANK,
            "Applies-to Doc. No.": "",
            "Bal. Account Type": "",
            "Bal. Account No.": "",
            "Signed": -1,
        },

        "credit memo_am_Total_(EUR)": {
            "Document Type": GenJournalDocumentType.PAYMENT,
            "Document No.": "",
            "Account Type": GenJournalAccountType.BANK_ACCOUNT,
            "Account No.": "",
            "Applies-to Doc. Type": GenJournalDocumentType.BLANK,
            "Applies-to Doc. No.": "",
            "Bal. Account Type": "",
            "Bal. Account No.": "",
            "Signed": 1,
        },



        # Commingling VAT, Order retrocharge, Other, Service Fees
        "gl_acc_am_Total_(EUR)": {
            "Document Type": GenJournalDocumentType.PAYMENT,
            "Document No.": "",
            "Account Type": GenJournalAccountType.GL_ACCOUNT,
            "Account No.": "GL2555",
            "Applies-to Doc. Type": GenJournalDocumentType.BLANK,
            "Applies-to Doc. No.": "",
            "Bal. Account Type": GenJournalAccountType.BANK_ACCOUNT,
            "Bal. Account No.": "BANK_AM",
            "Signed": -1
        }
    }

    RENAME = {
        "gl_acc_am_Total_(EUR)": "Amount",
        "invoice_am_amount_ex_fee": "Amount",
        "invoice_am_Amazon_fees": "Fees",
        "invoice_am_Total_(EUR)": "Net Total",
        "credit memo_am_amount_ex_fee": "Amount",
        "credit memo_am_Amazon_fees": "Fees",
        "credit memo_am_Total_(EUR)": "Net Total",
    }

    mask_cols = [
        "am_Order ID",
        "am_key",
        "cle_Entry No_",
        "cle_Customer No_",
        "cle_Document No_",
        "cle_External Document No_",
        "cle_key",
        "dcle_Entry No_",
        "dcle_Cust_ Ledger Entry No_",
        "dcle_Document No_",
        "AccountNo",
        "ExternalDocumentNo",
        "AppliesToDocNo",
        "BalAccountNo"
    ]
    
