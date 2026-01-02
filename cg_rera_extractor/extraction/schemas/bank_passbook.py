"""
Bank Passbook Schema

Schema for data extracted from Bank Account Passbooks.
"""

from typing import Optional, List, Dict
from pydantic import Field, validator
import re

from .base import BaseExtractionSchema


class BankPassbookSchema(BaseExtractionSchema):
    """
    Schema for Bank Passbook/Account extraction.
    
    RERA requires escrow accounts for project funds.
    This schema captures bank account details.
    """
    
    document_type: str = Field(default="bank_passbook")
    
    # Bank Details
    bank_name: Optional[str] = Field(None, description="Name of the bank")
    branch_name: Optional[str] = Field(None, description="Branch name")
    branch_code: Optional[str] = Field(None, description="Branch code")
    branch_address: Optional[str] = Field(None, description="Branch address")
    
    # Account Details
    account_number: Optional[str] = Field(None, description="Bank account number")
    account_type: Optional[str] = Field(
        None, 
        description="Type: Current/Savings/Escrow/Fixed Deposit"
    )
    account_holder_name: Optional[str] = Field(None, description="Account holder name")
    
    # IFSC/MICR
    ifsc_code: Optional[str] = Field(None, description="IFSC code")
    micr_code: Optional[str] = Field(None, description="MICR code")
    
    # Account Status
    opening_date: Optional[str] = Field(None, description="Account opening date (YYYY-MM-DD)")
    account_status: Optional[str] = Field(
        default="Active",
        description="Status: Active/Dormant/Closed"
    )
    
    # Balance Information (if visible)
    current_balance: Optional[str] = Field(None, description="Current balance with currency")
    opening_balance: Optional[str] = Field(None, description="Opening balance")
    
    # RERA Specific
    is_escrow_account: bool = Field(
        default=False,
        description="Whether this is a RERA escrow account"
    )
    linked_rera_number: Optional[str] = Field(
        None, 
        description="RERA registration number linked to this account"
    )
    
    @validator('ifsc_code')
    def validate_ifsc(cls, v):
        """Validate and normalize IFSC code"""
        if v:
            v = v.upper().replace(' ', '').replace('-', '')
            # IFSC format: 4 letters + 0 + 6 alphanumeric
            if re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', v):
                return v
            # Try to extract valid IFSC
            match = re.search(r'[A-Z]{4}0[A-Z0-9]{6}', v.upper())
            if match:
                return match.group(0)
        return v
    
    @validator('account_number')
    def validate_account_number(cls, v):
        """Clean account number"""
        if v:
            # Remove spaces and dashes
            return v.replace(' ', '').replace('-', '')
        return v
    
    @validator('account_type')
    def normalize_account_type(cls, v):
        """Normalize account type"""
        if v:
            v_lower = v.lower()
            if 'current' in v_lower:
                return 'Current Account'
            elif 'saving' in v_lower:
                return 'Savings Account'
            elif 'escrow' in v_lower:
                return 'Escrow Account'
            elif 'fixed' in v_lower or 'fd' in v_lower:
                return 'Fixed Deposit'
        return v
    
    def validate_extraction(self) -> bool:
        """Validate bank account extraction"""
        errors = []
        
        if not self.account_number:
            errors.append("Missing account number")
        
        if not self.bank_name:
            errors.append("Missing bank name")
        
        if not self.ifsc_code:
            errors.append("Missing IFSC code")
        
        self.validation_errors = errors
        self.is_valid = len(errors) == 0
        return self.is_valid
