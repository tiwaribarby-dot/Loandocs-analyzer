import os
import json
import base64
from PIL import Image
import PyPDF2
import io
from openai import OpenAI
from datetime import datetime
from dateutil import parser
import re

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user

class DocumentAnalyzer:
    def __init__(self, api_key=None):
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF file using PyPDF2"""
        try:
            pdf_file.seek(0)
            reader = PyPDF2.PdfReader(pdf_file)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            text = "\n".join(text_parts).strip()
            return text if text else None
        except Exception as e:
            print(f"[DEBUG] extract_text_from_pdf error: {e}")
            return None

        
    def encode_image_to_base64(self, image_file):
        """Convert image file to base64 for vision API"""
        try:
            image_file.seek(0)
            raw = image_file.read()
            image = Image.open(io.BytesIO(raw))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG", quality=95)
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"[DEBUG] encode_image_to_base64 error: {e}")
            return None

    def convert_pdf_to_images(self, pdf_file):
        """Convert all pages of PDF to base64 JPEG using PyMuPDF (no Poppler needed)"""
        try:
            import fitz  # PyMuPDF
            
            pdf_file.seek(0)
            pdf_bytes = pdf_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            if doc.page_count == 0:
                print("[DEBUG] Empty PDF file")
                return None

            # Convert all pages to images
            all_images_b64 = []
            for page_num in range(min(doc.page_count, 5)):  # Max 5 pages for efficiency
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=95)
                all_images_b64.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))
            
            doc.close()
            return all_images_b64
        except Exception as e:
            print(f"[DEBUG] convert_pdf_to_images error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def analyze_document_with_vision(self, file, file_type, analysis_prompt):
        """Use OpenAI GPT-5 to analyze document with improved error handling"""
        try:
            user_content = None
            
            if file_type == "pdf":
                text = self.extract_text_from_pdf(file)
                print(f"[DEBUG] extracted_text_length: {len(text) if text else 0}")

                if text and len(text.strip()) > 20:
                    user_content = f"{analysis_prompt}\n\nDocument Text:\n{text}\n\nIMPORTANT: Return ONLY valid JSON. Extract all visible information accurately."
                else:
                    print("[DEBUG] No text found, converting PDF to images...")
                    base64_images = self.convert_pdf_to_images(file)
                    if not base64_images or len(base64_images) == 0:
                        return {"error": "Unable to extract text or convert PDF to image. File may be corrupted."}
                    
                    # Build multi-image content for vision API
                    user_content = [
                        {"type": "text", "text": f"{analysis_prompt}\n\nThis is a scanned document with {len(base64_images)} page(s). Please analyze all pages carefully and extract all visible information. Return ONLY valid JSON."}
                    ]
                    
                    for idx, img_b64 in enumerate(base64_images):
                        user_content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                        })
                    
                    print(f"[DEBUG] Sending {len(base64_images)} images to GPT-5 vision API")

            elif file_type in ["jpg", "jpeg", "png"]:
                base64_image = self.encode_image_to_base64(file)
                if not base64_image:
                    return {"error": "Unable to encode image"}
                
                user_content = [
                    {"type": "text", "text": f"{analysis_prompt}\n\nPlease analyze this image carefully and extract all visible information. Return ONLY valid JSON."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            else:
                return {"error": f"Unsupported file type: {file_type}"}

            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-5",
                    messages=[
                        {"role": "system", "content": "You are an expert document analyzer specializing in financial and identity documents. Always return valid JSON with accurate data extraction. If a field is not visible, use null or 0 for numeric fields. Never make up data."},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"},
                    max_completion_tokens=3000
                )
                
                content = response.choices[0].message.content
                print(f"[DEBUG] AI Response length: {len(content)}")
                
                result = json.loads(content)
                print(f"[DEBUG] Successfully parsed JSON with keys: {result.keys()}")
                return result
                
            except json.JSONDecodeError as e_json:
                print(f"[DEBUG] JSON parse failed: {e_json}")
                return {"error": "Invalid JSON from AI model", "raw_response": content if 'content' in locals() else "No response"}
            except Exception as e_api:
                print(f"[DEBUG] OpenAI API call failed: {e_api}")
                return {"error": f"API call failed: {str(e_api)}"}

        except Exception as e:
            print(f"[DEBUG] analyze_document_with_vision exception: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Analysis failed: {str(e)}"}
    
    def identify_document_type(self, file, file_type):
        """Identify document type automatically"""
        prompt = """Analyze this document and identify its type. Return JSON with:
        {
            "document_type": "One of: salary_slip, bank_statement, pan_card, aadhar_card, form16, appointment_letter, loan_statement, property_document, other",
            "confidence": "high/medium/low",
            "reason": "Brief reason for classification"
        }
        
        Look for key indicators like:
        - PAN card: "Permanent Account Number", "Income Tax Department", 10-character alphanumeric PAN
        - Aadhar: "Aadhaar", 12-digit number, UIDAI logo
        - Salary slip: Monthly salary breakdown, earnings, deductions, employer name
        - Bank statement: Account number, transactions, bank logo
        """
        
        return self.analyze_document_with_vision(file, file_type, prompt)
    
    def analyze_salary_slip(self, file, file_type):
        """Analyze salary slip with enhanced extraction"""
        prompt = """Analyze this salary slip and extract COMPLETE information in JSON format.
        
        CRITICAL: Extract ALL amounts as NUMBERS (not strings). If a field is not visible, use 0.
        
        {
            "month": "Month and Year (e.g., 'January 2025')",
            "employee_name": "Full employee name",
            "employee_id": "Employee ID",
            "designation": "Job title/designation",
            "department": "Department name",
            "employer": "Company/employer name",
            "pan": "PAN number if visible",
            "uan": "UAN number if visible",
            "earnings": {
                "basic": 0,
                "hra": 0,
                "conveyance_allowance": 0,
                "travel_allowance": 0,
                "medical_allowance": 0,
                "special_allowance": 0,
                "lta": 0,
                "city_compensatory_allowance": 0,
                "education_allowance": 0,
                "other_allowances": 0,
                "incentive": 0,
                "overtime": 0,
                "bonus": 0,
                "commission": 0,
                "arrears": 0
            },
            "deductions": {
                "pf": 0,
                "esi": 0,
                "professional_tax": 0,
                "tds": 0,
                "loan_recovery": 0,
                "other_deductions": 0
            },
            "gross_salary": 0,
            "total_deductions": 0,
            "net_salary": 0,
            "employer_contribution": {
                "pf": 0,
                "esi": 0
            }
        }
        
        IMPORTANT:
        - All amounts must be numeric (not strings with currency symbols)
        - Look for earnings section and deductions section carefully
        - Map any allowance you find to the closest category
        - Gross salary = sum of all earnings
        - Net salary = gross salary - total deductions
        """
        
        return self.analyze_document_with_vision(file, file_type, prompt)
    
    def analyze_bank_statement(self, file, file_type):
        """Analyze bank statement with period validation"""
        prompt = """Analyze this bank statement and extract information in JSON format:
        {
            "account_holder": "Account holder name",
            "account_number": "Last 4 digits only",
            "bank_name": "Bank name",
            "statement_start_date": "Start date in DD/MM/YYYY format",
            "statement_end_date": "End date in DD/MM/YYYY format",
            "statement_period_months": 0,
            "average_balance": 0,
            "emis_found": [
                {
                    "lender": "Bank/NBFC name",
                    "emi_amount": 0,
                    "frequency": "monthly",
                    "loan_type": "home/personal/vehicle/gold/credit card",
                    "has_loan_document": false
                }
            ],
            "salary_credits": [
                {
                    "amount": 0,
                    "date": "DD/MM/YYYY",
                    "description": "Credit description"
                }
            ]
        }
        
        Calculate statement_period_months by counting months between start and end dates.
        Look for regular EMI debits (same amount, same day each month).
        DO NOT include SIPs, insurance premiums, or investments as EMIs.
        """
        
        result = self.analyze_document_with_vision(file, file_type, prompt)
        
        if 'error' not in result:
            result['is_six_months_statement'] = result.get('statement_period_months', 0) >= 6
            result['statement_warning'] = None if result.get('is_six_months_statement') else f"Statement covers only {result.get('statement_period_months', 0)} months. 6 months required."
        
        return result
    
    def analyze_form16(self, file, file_type):
        """Analyze Form 16 for income details"""
        prompt = """Analyze this Form 16 and extract information in JSON format:
        {
            "employee_name": "Employee name",
            "pan": "PAN number",
            "employer": "Employer name",
            "employer_tan": "TAN number",
            "financial_year": "Financial year (e.g., '2024-25')",
            "gross_salary": 0,
            "total_income": 0,
            "tax_deducted": 0,
            "standard_deduction": 0,
            "other_deductions": 0
        }
        
        Extract all amounts as numbers."""
        
        return self.analyze_document_with_vision(file, file_type, prompt)
    
    def analyze_identity_document(self, file, file_type, doc_type):
        """Analyze PAN or Aadhar card with improved extraction"""
        if doc_type.lower() == "pan":
            prompt = """Analyze this PAN card VERY CAREFULLY and extract ALL visible information in JSON format:
            {
                "name": "Full name exactly as shown on PAN card",
                "pan_number": "Complete 10-character PAN number (e.g., ABCDE1234F)",
                "father_name": "Father's name",
                "date_of_birth": "Date of birth in DD/MM/YYYY format"
            }
            
            CRITICAL INSTRUCTIONS:
            - The PAN number is ALWAYS 10 characters: 5 letters + 4 digits + 1 letter
            - Look carefully for the PAN number - it's usually prominently displayed
            - Extract the FULL name, not abbreviated
            - If father's name is not visible, use null
            - Date format must be DD/MM/YYYY
            
            DO NOT return masked values - extract the actual visible data."""
        else:
            prompt = """Analyze this Aadhar card and extract information in JSON format:
            {
                "name": "Full name on Aadhar",
                "aadhar_number": "Complete 12-digit number",
                "date_of_birth": "Date of birth in DD/MM/YYYY format",
                "gender": "Male/Female/Other",
                "address": "Complete address as shown"
            }
            
            Extract complete aadhar number (12 digits). Do not mask it."""
        
        return self.analyze_document_with_vision(file, file_type, prompt)
    
    def analyze_loan_statement(self, file, file_type):
        """Analyze loan statement or SOA"""
        prompt = """Analyze this loan statement and extract:
        {
            "borrower_name": "Borrower name",
            "lender": "Bank/NBFC name",
            "loan_type": "home/personal/vehicle/gold/other",
            "loan_account_number": "Last 4 digits",
            "emi_amount": 0,
            "outstanding_amount": 0,
            "loan_start_date": "DD/MM/YYYY",
            "tenure_months": 0,
            "interest_rate": 0,
            "is_closed": false
        }"""
        
        return self.analyze_document_with_vision(file, file_type, prompt)
    
    def analyze_generic_document(self, file, file_type):
        """Generic document analysis"""
        prompt = """Analyze this document and extract relevant information for a loan application:
        {
            "document_type": "Type of document identified",
            "key_information": "Summary of key information",
            "applicant_name": "Name if found",
            "relevant_dates": [],
            "amounts": [],
            "additional_details": "Other relevant information"
        }"""
        
        return self.analyze_document_with_vision(file, file_type, prompt)
    
    def analyze_with_custom_prompt(self, file, file_type, custom_instructions):
        """Allow user to provide custom AI instructions for re-analysis"""
        base_prompt = f"""You are analyzing a loan application document.
        
        User instructions: {custom_instructions}
        
        Analyze the document according to these instructions and return relevant information in JSON format.
        Always use numeric values for amounts (not strings).
        """
        
        return self.analyze_document_with_vision(file, file_type, base_prompt)
