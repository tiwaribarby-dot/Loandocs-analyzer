from fpdf import FPDF
from datetime import datetime
import pandas as pd

class LoanReportPDF(FPDF):
    """Custom PDF class for loan analysis reports"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        """Page header"""
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'LOAN APPLICATION ANALYSIS REPORT', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        """Page footer"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def section_title(self, title):
        """Add a section title"""
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(70, 130, 180)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, title, 0, 1, 'L', True)
        self.set_text_color(0, 0, 0)
        self.ln(3)
    
    def add_field(self, label, value):
        """Add a labeled field"""
        self.set_font('Arial', 'B', 10)
        self.cell(70, 7, f"{label}:", 0, 0)
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 7, str(value))
    
    def add_table(self, headers, data, col_widths=None):
        """Add a table to the PDF"""
        if not col_widths:
            col_widths = [190 / len(headers)] * len(headers)
        
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(200, 220, 255)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, 1, 0, 'C', True)
        self.ln()
        
        self.set_font('Arial', '', 8)
        for row in data:
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 7, str(cell), 1, 0, 'L')
            self.ln()
        self.ln(3)


class ReportGenerator:
    """Generate comprehensive PDF reports for loan applications"""
    
    def __init__(self):
        pass
    
    def generate_report(self, applicant_data, salary_analysis, eligibility_results, 
                       obligations, pending_docs, pending_forms, queries, 
                       output_filename="loan_analysis_report.pdf", bank_statement_data=None):
        """Generate complete PDF report with all sections including uploaded documents"""
        pdf = LoanReportPDF()
        pdf.add_page()
        
        pdf.set_font('Arial', 'I', 9)
        pdf.cell(0, 5, f"Generated on: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", 0, 1, 'R')
        pdf.ln(5)
        
        pdf.section_title('DOCUMENTS UPLOADED')
        
        if pending_docs.get('uploaded_documents_details'):
            for doc in pending_docs['uploaded_documents_details']:
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 6, f"- {doc['document_type']}", 0, 1)
                pdf.set_font('Arial', '', 9)
                
                if 'period' in doc:
                    pdf.cell(10)
                    pdf.cell(0, 5, f"  Period: {doc.get('period_start', 'N/A')} to {doc.get('period_end', 'N/A')} ({doc['period']})", 0, 1)
                if doc.get('warning'):
                    pdf.set_text_color(255, 0, 0)
                    pdf.cell(10)
                    pdf.cell(0, 5, f"  warning {doc['warning']}", 0, 1)
                    pdf.set_text_color(0, 0, 0)
        
        pdf.ln(5)
        
        pdf.section_title('1. APPLICANT SUMMARY')
        
        pdf.add_field('Applicant Name', applicant_data.get('applicant_name', 'N/A'))
        pdf.add_field('PAN', applicant_data.get('pan_masked', 'N/A'))
        pdf.add_field('Aadhar', applicant_data.get('aadhar_masked', 'N/A'))
        pdf.add_field('Date of Birth', applicant_data.get('date_of_birth', 'N/A'))
        pdf.add_field('Current Age', f"{applicant_data.get('current_age', 'N/A')} years")
        pdf.add_field('Mobile Number', applicant_data.get('mobile_no', 'N/A'))
        pdf.add_field('Email ID', applicant_data.get('email_id', 'N/A'))
        pdf.add_field('Current Address', applicant_data.get('current_address', 'N/A'))
        pdf.ln(3)
        
        pdf.add_field('Employment Type', 'Salaried')
        pdf.add_field('Employer/Company', applicant_data.get('employer', 'N/A'))
        pdf.add_field('Designation', applicant_data.get('designation', 'N/A'))
        pdf.add_field('Department', applicant_data.get('department', 'N/A'))
        pdf.add_field('Job Since', applicant_data.get('job_since', 'N/A'))
        pdf.add_field('Total Experience', applicant_data.get('total_experience', 'N/A'))
        pdf.add_field('Office Address', applicant_data.get('office_address', 'N/A'))
        pdf.ln(5)
        
        pdf.section_title('2. COMPLETE SALARY BREAKUP (Last 3 Months)')
        
        if salary_analysis.get('salary_slips') and len(salary_analysis['salary_slips']) > 0:
            for slip in salary_analysis['salary_slips'][:3]:
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 7, f"Month: {slip.get('month', 'N/A')}", 0, 1)
                pdf.ln(2)
                
                earnings = slip.get('earnings', {})
                deductions = slip.get('deductions', {})
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 6, 'EARNINGS:', 0, 1)
                pdf.set_font('Arial', '', 9)
                
                earning_items = [
                    ('Basic Salary', earnings.get('basic', 0)),
                    ('HRA', earnings.get('hra', 0)),
                    ('Conveyance Allowance', earnings.get('conveyance_allowance', 0)),
                    ('Travel Allowance', earnings.get('travel_allowance', 0)),
                    ('Medical Allowance', earnings.get('medical_allowance', 0)),
                    ('Special Allowance', earnings.get('special_allowance', 0)),
                    ('LTA', earnings.get('lta', 0)),
                    ('City Compensatory Allowance', earnings.get('city_compensatory_allowance', 0)),
                    ('Education Allowance', earnings.get('education_allowance', 0)),
                    ('Other Allowances', earnings.get('other_allowances', 0)),
                    ('Incentive', earnings.get('incentive', 0)),
                    ('Overtime', earnings.get('overtime', 0)),
                    ('Bonus', earnings.get('bonus', 0)),
                    ('Commission', earnings.get('commission', 0)),
                    ('Arrears', earnings.get('arrears', 0))
                ]
                
                for item, value in earning_items:
                    if value > 0:
                        pdf.cell(120, 5, f"  {item}", 0, 0)
                        pdf.cell(0, 5, f"Rs {value:,.2f}", 0, 1, 'R')
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(120, 6, 'GROSS SALARY', 0, 0)
                pdf.cell(0, 6, f"Rs {slip.get('gross_salary', 0):,.2f}", 0, 1, 'R')
                pdf.ln(2)
                
                pdf.cell(0, 6, 'DEDUCTIONS:', 0, 1)
                pdf.set_font('Arial', '', 9)
                
                deduction_items = [
                    ('PF', deductions.get('pf', 0)),
                    ('ESI', deductions.get('esi', 0)),
                    ('Professional Tax', deductions.get('professional_tax', 0)),
                    ('TDS', deductions.get('tds', 0)),
                    ('Loan Recovery', deductions.get('loan_recovery', 0)),
                    ('Other Deductions', deductions.get('other_deductions', 0))
                ]
                
                for item, value in deduction_items:
                    if value > 0:
                        pdf.cell(120, 5, f"  {item}", 0, 0)
                        pdf.cell(0, 5, f"Rs {value:,.2f}", 0, 1, 'R')
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(120, 6, 'TOTAL DEDUCTIONS', 0, 0)
                pdf.cell(0, 6, f"Rs {slip.get('total_deductions', 0):,.2f}", 0, 1, 'R')
                pdf.ln(2)
                
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(120, 7, 'NET SALARY', 0, 0)
                pdf.cell(0, 7, f"Rs {slip.get('net_salary', 0):,.2f}", 0, 1, 'R')
                pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 7, 'Income Calculation Summary:', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        gross_income = eligibility_results.get('calculations', {}).get('gross_monthly_income', 0)
        fixed_income = eligibility_results.get('calculations', {}).get('fixed_income', 0)
        variable_income = eligibility_results.get('calculations', {}).get('variable_income_considered', 0)
        
        pdf.add_field('  Fixed Components (100%)', f"Rs{fixed_income:,.2f}")
        pdf.add_field('  Variable Components (50% of 6-month avg)', f"Rs{variable_income:,.2f}")
        pdf.set_font('Arial', 'B', 11)
        pdf.add_field('  GROSS MONTHLY INCOME', f"Rs{gross_income:,.2f}")
        pdf.ln(5)
        
        pdf.section_title('3. LOAN ELIGIBILITY SUMMARY')
        
        calculations = eligibility_results.get('calculations', {})
        
        pdf.add_field('Requested Loan Amount', f"Rs{applicant_data.get('loan_amount', 0):,.0f}")
        pdf.add_field('Tenure (Auto-calculated based on age)', f"{calculations.get('approved_tenure_years', 'N/A')} years")
        pdf.add_field('Interest Rate', f"{applicant_data.get('interest_rate', 8.5)}% p.a.")
        pdf.ln(2)
        
        pdf.add_field('Current Age', f"{calculations.get('current_age', 'N/A')} years")
        pdf.add_field('Maximum Age Limit', '60 years')
        pdf.add_field('Remaining Service Years', f"{calculations.get('remaining_service_years', 'N/A')} years")
        pdf.add_field('Maximum Tenure Allowed', f"{calculations.get('max_tenure_allowed', 'N/A')} years")
        pdf.ln(2)
        
        pdf.add_field('Current FOIR (before new loan)', f"{calculations.get('current_foir_percent', 0):.2f}%")
        pdf.add_field('FOIR with Requested Loan', f"{calculations.get('foir_with_requested_loan', 0):.2f}%")
        pdf.add_field('Maximum FOIR Allowed', '60.00%')
        pdf.ln(2)
        
        pdf.add_field('EMI for Requested Loan', f"Rs{calculations.get('emi_for_requested_loan', 0):,.2f}")
        pdf.add_field('Maximum EMI Capacity', f"Rs{calculations.get('max_emi_allowed', 0):,.2f}")
        pdf.add_field('Maximum Loan by Income', f"Rs{calculations.get('max_loan_by_income', 0):,.2f}")
        pdf.ln(3)
        
        pdf.set_font('Arial', 'B', 12)
        if eligibility_results.get('eligible'):
            pdf.set_text_color(0, 128, 0)
            pdf.cell(0, 10, 'ELIGIBLE FOR LOAN', 0, 1)
            approved_amount = calculations.get('approved_loan_amount', 0)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, f'Approved Amount: Rs{approved_amount:,.0f}', 0, 1)
        else:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 10, 'NOT ELIGIBLE AS PER CURRENT NORMS', 0, 1)
            recommended = calculations.get('recommended_loan_amount', 0)
            if recommended > 0:
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 7, f'Recommended Amount: Rs{recommended:,.0f}', 0, 1)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)
        
        if eligibility_results.get('issues'):
            pdf.set_font('Arial', 'B', 10)
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 7, 'Issues:', 0, 1)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 9)
            for issue in eligibility_results['issues']:
                pdf.multi_cell(0, 5, f"  - {issue}")
        
        if eligibility_results.get('warnings'):
            pdf.set_font('Arial', 'B', 10)
            pdf.set_text_color(255, 140, 0)
            pdf.cell(0, 7, 'Warnings:', 0, 1)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 9)
            for warning in eligibility_results['warnings']:
                pdf.multi_cell(0, 5, f"  - {warning}")
        
        pdf.ln(5)
        
        pdf.section_title('4. EXISTING OBLIGATIONS / EMI DETAILS')
        
        if obligations and len(obligations) > 0:
            headers = ['Lender/Bank', 'Loan Type', 'Monthly EMI', 'Status']
            data = []
            total_emi = 0
            
            for obl in obligations:
                lender = obl.get('lender', 'Unknown')
                loan_type = obl.get('type', 'Unknown')
                amount = obl.get('amount', 0)
                excluded = obl.get('excluded', False)
                has_doc = obl.get('has_loan_document', False)
                
                if not excluded:
                    total_emi += amount
                
                status = 'Excluded' if excluded else 'Active'
                data.append([lender, loan_type.title(), f"Rs{amount:,.2f}", status])
            
            data.append(['', '', f"Rs{total_emi:,.2f}", 'TOTAL'])
            
            pdf.add_table(headers, data, [60, 45, 40, 45])
        else:
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 7, 'No existing loan obligations identified', 0, 1)
            pdf.ln(3)
        
        pdf.add_field('Total Existing Obligations (considered)', f"Rs{calculations.get('total_existing_obligations', 0):,.2f} per month")
        pdf.ln(5)
        
        pdf.section_title('5. PENDING DOCUMENTS')
        
        pending_doc_list = pending_docs.get('pending_documents', [])
        if pending_doc_list:
            pdf.set_font('Arial', '', 10)
            for i, doc in enumerate(pending_doc_list, 1):
                pdf.multi_cell(0, 6, f"{i}. {doc}")
        else:
            pdf.set_font('Arial', 'B', 10)
            pdf.set_text_color(0, 128, 0)
            pdf.cell(0, 7, 'All mandatory documents uploaded', 0, 1)
            pdf.set_text_color(0, 0, 0)
        
        pdf.ln(3)
        pdf.add_field('Document Completion', f"{pending_docs.get('completion_percentage', 0)}%")
        pdf.ln(5)
        
        pdf.section_title('6. PENDING FORM DETAILS')
        
        pending_field_list = pending_forms.get('pending_form_fields', [])
        if pending_field_list:
            pdf.set_font('Arial', '', 10)
            for i, field in enumerate(pending_field_list, 1):
                pdf.multi_cell(0, 6, f"{i}. {field}")
        else:
            pdf.set_font('Arial', 'B', 10)
            pdf.set_text_color(0, 128, 0)
            pdf.cell(0, 7, 'All form details complete', 0, 1)
            pdf.set_text_color(0, 0, 0)
        
        pdf.ln(3)
        pdf.add_field('Form Completion', f"{pending_forms.get('completion_percentage', 0)}%")
        pdf.ln(5)
        
        pdf.section_title('7. PROBABLE QUERIES')
        
        if queries and len(queries) > 0:
            pdf.set_font('Arial', '', 9)
            for query in queries:
                pdf.multi_cell(0, 5, query)
                pdf.ln(1)
        else:
            pdf.set_font('Arial', 'B', 10)
            pdf.set_text_color(0, 128, 0)
            pdf.cell(0, 7, 'No queries identified. File appears complete.', 0, 1)
            pdf.set_text_color(0, 0, 0)
        
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 5, 'Note: This is an AI-generated analysis. Please verify all information with actual documents. '
                            'Aadhar numbers are masked showing only last 4 digits. PAN numbers are masked showing only last 4 characters.')
        
        pdf.output(output_filename)
        return output_filename
