import logging
from dataclasses import dataclass
from enum import Enum

# https://learn.microsoft.com/en-us/dynamics365/business-central/application/base-application/table/microsoft.finance.generalledger.journal.gen.-journal-line


class GenJournalDocumentType(Enum):
    BLANK = " "
    PAYMENT = "Payment"
    INVOICE = "Invoice"
    CREDIT_MEMO = "Credit Memo"
    FINANCE_CHARGE_MEMO = "Finance Charge Memo"
    REMINDER = "Reminder"
    REFUND = "Refund"


class GenJournalAccountType(Enum):
    GL_ACCOUNT = "G/L Account"
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    BANK_ACCOUNT = "Bank Account"
    FIXED_ASSET = "Fixed Asset"
    IC_PARTNER = "IC Partner"
    EMPLOYEE = "Employee"
    ALLOCATION_ACCOUNT = "Allocation Account"

@dataclass
class GenJournalLine:
    JournalTemplateName: str
    JournalBatchName: str
    DocumentType: GenJournalDocumentType
    DocumentNo: str
    LineNo: int
    AccountType: GenJournalAccountType
    AccountNo: str
    PostingDate: str
    Description: str
    ExternalDocumentNo: str
    CurrencyCode: str
    Amount: float
    SourceCode: str
    AppliesToDocType: GenJournalDocumentType
    AppliesToDocNo: str
    BalAccountType: GenJournalAccountType
    BalAccountNo: str


    def create_document_no(line_no, row):
        # Create document numbers from date and journal line number
        date = row['am_Date'].strftime("%Y%m%d")
        return f"PMTAM{date}{int(line_no)}"
    

    @staticmethod
    def get_value(posting_type, field_name, row):
        # Look up the field in the posting_type dictionary
        value = posting_type[field_name]

        # If it's a function (lambda), call it with row
        if callable(value):
            value = value(row)

        # If it's an Enum, normalize to its .value string
        if hasattr(value, "value"):
            value = value.value

        # Applies-to Doc. No. can only apply if the invoice or credit memo is open
        if field_name == "Applies-to Doc. No." and row["cle_Open"] != "Yes":
            return ""

        # Otherwise just return the value
        return value


    @classmethod
    def create_gen_journal_line(cls, line_no, row, posting_type):

        journal_line = cls(
            JournalTemplateName = "PMTAM",
            JournalBatchName = "PMTAM",
            DocumentType = cls.get_value(posting_type, "Document Type", row),
            DocumentNo = cls.create_document_no(line_no, row),
            PostingDate = row["am_Date"].strftime("%d-%m-%Y"),
            LineNo = line_no,
            AccountType = cls.get_value(posting_type, "Account Type", row),
            AccountNo = cls.get_value(posting_type, "Account No.", row),
            Description = row["posting_description"],
            ExternalDocumentNo = row["am_Order ID"],
            CurrencyCode = "EUR",
            Amount = row["Amount"] * posting_type.get("Signed"),
            SourceCode = "PMTJNL",
            AppliesToDocType = cls.get_value(posting_type, "Applies-to Doc. Type", row),
            AppliesToDocNo = cls.get_value(posting_type, "Applies-to Doc. No.", row),
            BalAccountType = cls.get_value(posting_type, "Bal. Account Type", row),
            BalAccountNo = cls.get_value(posting_type, "Bal. Account No.", row)
        )
        return journal_line
