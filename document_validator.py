from datetime import datetime
from dateutil import parser

class DocumentValidator:
    """Validates uploaded documents against requirements"""
    
    def __init__(self):
        self.MANDATORY_DOCUMENTS = {
            'aadhar': 'Aadhar Card',
            'pan': 'PAN Card',
            'salary_slips': 'Latest 3 Months Salary Slips',
            'form16': 'Form 16 (with Part A and Part B)',
            'bank_statement': '6 Months Bank Statement',
        }
        
        self.CONDITIONAL_DOCUMENTS = {
            'appointment_letter': 'Appointment Letter (if job < 3 years)',
            'resume': 'Resume (if job < 3 years)',
            'loan_statements': 'Loan Statement/SOA (if EMI found in bank statement)',
            'property_documents': 'Property Documents',
            'employer_letter': 'Employer Letterg/Verification',
        }
        
        self.REQUIRED_FORM_FIELDS = {
            'applicant_name': 'Applicant Name',
            'spouse_name': 'Applicant Spouse Name',
            'mother_name': 'Mother Name',
            'current_address': 'Current Address',
            'mobile_no': 'Mobile Number',
            'email_id': 'Email ID',
            'children': 'Children Details',
            'qualification': 'Qualification',
            'office_address': 'Office Address',
            'office_landline': 'Office Landline Number',
            'official_email': 'Official Email ID',
            'job_since': 'Job Since (Date)',
            'total_experience': 'Total Experience',
            'department': 'Department',
            'designation': 'Designation',
            'loan_amount': 'Loan Amount Requested',
            'tenure': 'Loan Tenure',
            'investment_details': 'Investment Details',
            'property_address': 'Property Address',
            'property_type': 'Property Type (Builder/Resale)',
            'property_pincode': 'Property Pincode',
            'property_carpet_area': 'Property Carpet Area',
            'saledeed_amount': 'Sale Deed Amount',
            'reference1_name': 'Reference 1 - Name',
            'reference1_mobile': 'Reference 1 - Mobile',
            'reference1_email': 'Reference 1 - Email',
            'reference1_address': 'Reference 1 - Address',
            'reference2_name': 'Reference 2 - Name',
            'reference2_mobile': 'Reference 2 - Mobile',
            'reference2_email': 'Reference 2 - Email',
            'reference2_address': 'Reference 2 - Address',
        }
    
    def check_pending_documents(self, uploaded_docs, analyzed_results=None):
        """Check which mandatory documents are missing and track uploaded ones"""
        pending = []
        uploaded = []
        uploaded_details = []
        
        for doc_key, doc_name in self.MANDATORY_DOCUMENTS.items():
            if doc_key == 'salary_slips':
                count = uploaded_docs.get(doc_key, 0)
                if count < 3:
                    pending.append(f"{doc_name} - Found {count}/3 required")
                else:
                    uploaded.append(f"{doc_name} - Complete ({count} slips)")
                    uploaded_details.append({
                        'document_type': doc_name,
                        'count': count,
                        'status': 'Complete'
                    })
            elif doc_key == 'bank_statement':
                if uploaded_docs.get(doc_key):
                    bank_data = analyzed_results.get('bank_statement', {}) if analyzed_results else {}
                    period_months = bank_data.get('statement_period_months', 0)
                    
                    if period_months < 6:
                        pending.append(f"{doc_name} - Only {period_months} months found (6 months required)")
                        uploaded_details.append({
                            'document_type': doc_name,
                            'period': f"{period_months} months",
                            'status': 'Incomplete',
                            'warning': f"Only {period_months} months provided, 6 months required"
                        })
                    else:
                        uploaded.append(f"{doc_name} - Complete ({period_months} months)")
                        uploaded_details.append({
                            'document_type': doc_name,
                            'period': f"{period_months} months",
                            'period_start': bank_data.get('statement_start_date', 'N/A'),
                            'period_end': bank_data.get('statement_end_date', 'N/A'),
                            'status': 'Complete'
                        })
                else:
                    pending.append(doc_name)
            else:
                if not uploaded_docs.get(doc_key):
                    pending.append(doc_name)
                else:
                    uploaded.append(f"{doc_name} - Uploaded")
                    uploaded_details.append({
                        'document_type': doc_name,
                        'status': 'Uploaded'
                    })
        
        return {
            'pending_documents': pending,
            'uploaded_documents': uploaded,
            'uploaded_documents_details': uploaded_details,
            'completion_percentage': round((len(uploaded) / len(self.MANDATORY_DOCUMENTS)) * 100, 1)
        }
    
    def check_conditional_documents(self, uploaded_docs, conditions, emis_list=None):
      """Check conditional documents including loan documents for identified EMIs"""
      additional_required = []
    
      if conditions.get('job_less_than_3_years'):
        if not uploaded_docs.get('appointment_letter'):
            additional_required.append(self.CONDITIONAL_DOCUMENTS['appointment_letter'])
        if not uploaded_docs.get('resume'):
            additional_required.append(self.CONDITIONAL_DOCUMENTS['resume'])
    
      if emis_list and len(emis_list) > 0:
        for emi in emis_list:
            if not emi.get('has_loan_document', False):
                loan_type = (emi.get('loan_type') or 'Unknown').title()
                lender = emi.get('lender') or 'Unknown Lender'
                additional_required.append(
                    f"Loan Statement/SOA for {loan_type} loan with {lender}"
                )
    
      return additional_required
    
    def check_pending_form_details(self, extracted_data):
        """Check which form fields are missing"""
        pending_fields = []
        filled_fields = []
        
        for field_key, field_name in self.REQUIRED_FORM_FIELDS.items():
            value = extracted_data.get(field_key)
            
            if not value or value == "" or value == "Not found" or value == "N/A":
                pending_fields.append(field_name)
            else:
                filled_fields.append(f"{field_name} - Filled")
        
        return {
            'pending_form_fields': pending_fields,
            'filled_form_fields': filled_fields,
            'completion_percentage': round((len(filled_fields) / len(self.REQUIRED_FORM_FIELDS)) * 100, 1)
        }
    
    def validate_aadhar_format(self, aadhar_number):
        """Validate and mask Aadhar number"""
        if not aadhar_number:
            return None
        
        clean_aadhar = ''.join(filter(str.isdigit, str(aadhar_number)))
        
        if len(clean_aadhar) == 12:
            return f"XXXX XXXX {clean_aadhar[-4:]}"
        return aadhar_number
    
    def validate_pan_format(self, pan_number):
        """Validate and mask PAN number"""
        if not pan_number:
            return None
        
        clean_pan = str(pan_number).replace(" ", "").upper()
        
        if len(clean_pan) == 10:
            return f"XXXXXX{clean_pan[-4:]}"
        return pan_number
    
    def extract_form_data_from_documents(self, all_analyzed_docs):
        """Compile form data from all analyzed documents"""
        form_data = {}
        
        if 'salary_slips' in all_analyzed_docs and len(all_analyzed_docs['salary_slips']) > 0:
            latest_slip = all_analyzed_docs['salary_slips'][0]
            form_data['applicant_name'] = latest_slip.get('employee_name', '')
            form_data['designation'] = latest_slip.get('designation', '')
            form_data['department'] = latest_slip.get('department', '')
            form_data['office_address'] = latest_slip.get('employer', '')
        
        if 'pan' in all_analyzed_docs:
            pan_data = all_analyzed_docs.get('pan') or {}
            
            if not form_data.get('applicant_name'):
                form_data['applicant_name'] = pan_data.get('name', '')
            form_data['mother_name'] = pan_data.get('father_name', '')

        if 'aadhar' in all_analyzed_docs:
            aadhar_data = all_analyzed_docs.get('aadhar') or {}
            
            if not form_data.get('applicant_name'):
                form_data['applicant_name'] = aadhar_data.get('name', '')
            
            form_data['current_address'] = aadhar_data.get('address', '')

        if 'form16' in all_analyzed_docs:
            f16_data = all_analyzed_docs.get('form16') or {}
            
            if not form_data.get('applicant_name'):
                form_data['applicant_name'] = f16_data.get('employee_name', '')

        if 'bank_statement' in all_analyzed_docs:
            bank_data = all_analyzed_docs.get('bank_statement') or {}
            
            if not form_data.get('applicant_name'):
                form_data['applicant_name'] = bank_data.get('account_holder', '')

        return form_data
