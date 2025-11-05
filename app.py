import streamlit as st
import os
from datetime import datetime
from document_analyzer import DocumentAnalyzer
from loan_calculator import LoanEligibilityCalculator
from document_validator import DocumentValidator
from query_generator import QueryGenerator
from report_generator import ReportGenerator
import io

st.set_page_config(
    page_title="AI Loan Document Analysis",
    page_icon="📄",
    layout="wide"
)

if 'analyzed_data' not in st.session_state:
    st.session_state.analyzed_data = None
if 'all_uploaded_files' not in st.session_state:
    st.session_state.all_uploaded_files = []
if 'categorized_docs' not in st.session_state:
    st.session_state.categorized_docs = {}
if 'excluded_emis' not in st.session_state:
    st.session_state.excluded_emis = []
if 'loan_config' not in st.session_state:
    st.session_state.loan_config = {
        'foir_salaried': 60,
        'max_age_salaried': 60,
        'max_tenure_years': 30,
        'min_income_threshold': 25000,
        'high_foir_threshold': 40
    }

def main():
    st.title("🏦 AI-Powered Loan Document Analysis System")
    st.markdown("Upload customer documents - AI will automatically categorize and analyze using GPT-5")
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.subheader("🔧 Loan Policy Settings")
        with st.expander("📋 View/Edit Loan Policy", expanded=False):
            st.markdown("**Current Loan Policy:**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.loan_config['foir_salaried'] = st.number_input(
                    "FOIR % (Salaried)",
                    min_value=40,
                    max_value=90,
                    value=st.session_state.loan_config['foir_salaried'],
                    step=5,
                    help="Fixed Obligation to Income Ratio limit - maximum % of income for EMIs"
                )
                
                st.session_state.loan_config['max_tenure_years'] = st.number_input(
                    "Maximum Tenure (Years)",
                    min_value=10,
                    max_value=40,
                    value=st.session_state.loan_config['max_tenure_years'],
                    step=5,
                    help="Maximum loan tenure allowed"
                )
            
            with col2:
                st.session_state.loan_config['max_age_salaried'] = st.number_input(
                    "Maximum Age (Salaried)",
                    min_value=55,
                    max_value=70,
                    value=st.session_state.loan_config['max_age_salaried'],
                    step=1,
                    help="Maximum age at loan maturity"
                )
                
                st.session_state.loan_config['min_income_threshold'] = st.number_input(
                    "Minimum Income (₹)",
                    min_value=10000,
                    max_value=50000,
                    value=st.session_state.loan_config['min_income_threshold'],
                    step=5000,
                    help="Minimum monthly income required"
                )
            
            if st.button("💾 Apply Policy Changes", use_container_width=True):
                st.success("✅ Loan policy updated!")
                st.rerun()
        
        st.markdown("---")
        
        st.subheader("Loan Details")
        requested_amount = st.number_input(
            "Requested Loan Amount (₹)",
            min_value=100000,
            max_value=50000000,
            value=5200000,
            step=100000
        )
        
        interest_rate = st.number_input(
            "Interest Rate (% p.a.)",
            min_value=6.0,
            max_value=15.0,
            value=8.5,
            step=0.1,
            help="Tenure is auto-calculated based on applicant age"
        )
        
        st.info("ℹ️ Tenure = Max Age - Current Age (max 30 years)")
        
        st.markdown("---")
        st.markdown("### 📋 Auto-detects:")
        st.markdown("""
        - PAN Card
        - Aadhar Card  
        - Salary Slips (3 months)
        - Form 16
        - Bank Statements
        - Loan Statements
        """)
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload Documents", "📊 Analysis Results", "🔄 Recalculate"])
    
    with tab1:
        st.header("Upload All Customer Documents")
        st.info("📁 Upload all documents - AI will identify and categorize each one using advanced vision analysis")
        
        uploaded_files = st.file_uploader(
            "Drop documents here (PDF, JPG, PNG)",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            key='all_docs',
            help="Upload salary slips, bank statements, ID proofs, etc."
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
            
            with st.expander("📋 Uploaded Files", expanded=True):
                for i, file in enumerate(uploaded_files, 1):
                    st.write(f"{i}. {file.name}")
        
        st.markdown("---")
        
        if st.button("🔍 Analyze All Documents", type="primary", use_container_width=True):
            if not os.environ.get("OPENAI_API_KEY"):
                st.error("❌ OpenAI API Key not configured!")
            elif not uploaded_files:
                st.error("Please upload at least one document!")
            else:
                analyze_all_documents(uploaded_files, requested_amount, interest_rate)
    
    with tab2:
        if st.session_state.analyzed_data:
            display_results(st.session_state.analyzed_data)
        else:
            st.info("👈 Upload documents and click 'Analyze All Documents'")
    
    with tab3:
        st.header("🔄 Recalculate with Different Parameters")
        
        if st.session_state.analyzed_data:
            st.markdown("### Option 1: Exclude EMIs and Recalculate")
            st.info("Check the boxes below to exclude specific EMIs (e.g., customer is closing the loan)")
            
            if st.session_state.analyzed_data.get('obligations'):
                for i, obl in enumerate(st.session_state.analyzed_data['obligations']):
                    col1, col2, col3 = st.columns([4, 2, 2])
                    
                    with col1:
                        st.write(f"**{obl['lender']}** - {obl['type'].title()} Loan")
                    
                    with col2:
                        st.write(f"₹{obl['amount']:,.0f}/month")
                    
                    with col3:
                        is_excluded = st.checkbox(
                            "Exclude from calculation",
                            key=f"exclude_emi_{i}",
                            value=i in st.session_state.excluded_emis
                        )
                        
                        if is_excluded and i not in st.session_state.excluded_emis:
                            st.session_state.excluded_emis.append(i)
                            recalculate_eligibility(requested_amount, interest_rate)
                            st.rerun()
                        elif not is_excluded and i in st.session_state.excluded_emis:
                            st.session_state.excluded_emis.remove(i)
                            recalculate_eligibility(requested_amount, interest_rate)
                            st.rerun()
                
                total_excluded = sum(obl['amount'] for i, obl in enumerate(st.session_state.analyzed_data['obligations']) if i in st.session_state.excluded_emis)
                if total_excluded > 0:
                    st.success(f"💰 Excluded EMIs: ₹{total_excluded:,.0f}/month")
            else:
                st.info("No EMIs found to exclude")
            
            st.markdown("---")
            st.markdown("### Option 2: Adjust Loan Amount/Interest")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                new_loan_amount = st.number_input(
                    "New Loan Amount (₹)",
                    min_value=100000,
                    max_value=50000000,
                    value=int(st.session_state.analyzed_data['applicant_info'].get('loan_amount', requested_amount)),
                    step=100000,
                    key="new_loan_amt"
                )
            
            with col_b:
                new_interest_rate = st.number_input(
                    "New Interest Rate (%)",
                    min_value=6.0,
                    max_value=15.0,
                    value=float(st.session_state.analyzed_data['applicant_info'].get('interest_rate', interest_rate)),
                    step=0.1,
                    key="new_int_rate"
                )
            
            with col_c:
                st.write("")
                st.write("")
                if st.button("🔄 Recalculate", type="primary", use_container_width=True):
                    recalculate_eligibility(new_loan_amount, new_interest_rate)
                    st.success("✅ Recalculated!")
                    st.rerun()
        else:
            st.info("Analyze documents first to enable recalculation")


def get_file_type(file):
    """Determine file type from filename"""
    if file.name.lower().endswith('.pdf'):
        return 'pdf'
    elif file.name.lower().endswith(('.jpg', '.jpeg')):
        return 'jpg'
    elif file.name.lower().endswith('.png'):
        return 'png'
    return 'unknown'


def analyze_all_documents(uploaded_files, requested_amount, interest_rate):
    """Main analysis function with auto document categorization"""
    
    with st.spinner("🤖 AI is analyzing documents with GPT-5... This may take a few minutes..."):
        try:
            doc_analyzer = DocumentAnalyzer(api_key=os.environ.get("OPENAI_API_KEY"))
            loan_calc = LoanEligibilityCalculator(config=st.session_state.loan_config)
            validator = DocumentValidator()
            query_gen = QueryGenerator()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            categorized = {
                'salary_slips': [],
                'bank_statements': [],
                'pan': None,
                'aadhar': None,
                'form16': None,
                'loan_statements': [],
                'other': []
            }
            
            all_analyzed = {}
            applicant_info = {
                'loan_amount': requested_amount,
                'interest_rate': interest_rate
            }
            
            total_files = len(uploaded_files)
            
            for idx, file in enumerate(uploaded_files):
                file_type = get_file_type(file)
                progress = int((idx / total_files) * 40)
                progress_bar.progress(progress)
                status_text.text(f"🔍 Analyzing {idx + 1}/{total_files}: {file.name}...")
                
                file.seek(0)
                doc_type_result = doc_analyzer.identify_document_type(file, file_type)
                
                if 'error' in doc_type_result:
                    st.warning(f"⚠️ Could not identify {file.name}: {doc_type_result['error']}")
                    continue
                
                doc_type = doc_type_result.get('document_type', 'other')
                status_text.text(f"✓ Identified as {doc_type.replace('_', ' ').title()}")
                
                file.seek(0)
                
                if doc_type == 'salary_slip':
                    result = doc_analyzer.analyze_salary_slip(file, file_type)
                    if 'error' not in result:
                        categorized['salary_slips'].append(result)
                        if not applicant_info.get('employer'):
                            applicant_info['employer'] = result.get('employer', 'N/A')
                        if not applicant_info.get('designation'):
                            applicant_info['designation'] = result.get('designation', 'N/A')
                        if not applicant_info.get('department'):
                            applicant_info['department'] = result.get('department', 'N/A')
                
                elif doc_type == 'bank_statement':
                    result = doc_analyzer.analyze_bank_statement(file, file_type)
                    if 'error' not in result:
                        categorized['bank_statements'].append(result)
                
                elif doc_type == 'pan_card':
                    result = doc_analyzer.analyze_identity_document(file, file_type, 'pan')
                    categorized['pan'] = result
                    if 'error' not in result:
                        applicant_info['pan_masked'] = validator.validate_pan_format(result.get('pan_number'))
                        if not applicant_info.get('applicant_name'):
                            applicant_info['applicant_name'] = result.get('name', 'N/A')
                
                elif doc_type == 'aadhar_card':
                    result = doc_analyzer.analyze_identity_document(file, file_type, 'aadhar')
                    categorized['aadhar'] = result
                    if 'error' not in result:
                        applicant_info['aadhar_masked'] = validator.validate_aadhar_format(result.get('aadhar_number'))
                        if not applicant_info.get('applicant_name'):
                            applicant_info['applicant_name'] = result.get('name', 'N/A')
                        applicant_info['date_of_birth'] = result.get('date_of_birth')
                        applicant_info['current_address'] = result.get('address', 'N/A')
                
                elif doc_type == 'form16':
                    result = doc_analyzer.analyze_form16(file, file_type)
                    categorized['form16'] = result
                    if 'error' not in result:
                        if not applicant_info.get('employer'):
                            applicant_info['employer'] = result.get('employer', 'N/A')
                
                elif doc_type == 'loan_statement':
                    result = doc_analyzer.analyze_loan_statement(file, file_type)
                    if 'error' not in result:
                        categorized['loan_statements'].append(result)
                
                else:
                    result = doc_analyzer.analyze_generic_document(file, file_type)
                    categorized['other'].append(result)
            
            all_analyzed['salary_slips'] = categorized['salary_slips']
            all_analyzed['pan'] = categorized['pan']
            all_analyzed['aadhar'] = categorized['aadhar']
            all_analyzed['form16'] = categorized['form16']
            
            status_text.text("📊 Processing bank statements and EMIs...")
            progress_bar.progress(50)
            
            all_emis = []
            bank_statement_data = None
            for stmt in categorized['bank_statements']:
                emis_found = stmt.get('emis_found', [])
                all_emis.extend(emis_found)
                if not bank_statement_data:
                    bank_statement_data = stmt
                    all_analyzed['bank_statement'] = stmt
            
            for loan_stmt in categorized['loan_statements']:
                for emi in all_emis:
                    if emi.get('lender') == loan_stmt.get('lender'):
                        emi['has_loan_document'] = True
            
            if applicant_info.get('date_of_birth'):
                age = loan_calc.calculate_age(applicant_info['date_of_birth'])
                applicant_info['current_age'] = age
            
            status_text.text("💰 Calculating eligibility...")
            progress_bar.progress(70)
            
            auto_tenure = loan_calc.calculate_auto_tenure(applicant_info.get('current_age', 30))
            applicant_info['tenure'] = auto_tenure
            
            eligibility = loan_calc.calculate_eligibility(
                applicant_info,
                categorized['salary_slips'],
                all_emis,
                requested_amount,
                None,
                interest_rate,
                st.session_state.excluded_emis
            )
            
            status_text.text("📋 Validating documents...")
            progress_bar.progress(85)
            
            uploaded_docs = {
                'aadhar': categorized['aadhar'] is not None,
                'pan': categorized['pan'] is not None,
                'salary_slips': len(categorized['salary_slips']),
                'form16': categorized['form16'] is not None,
                'bank_statement': len(categorized['bank_statements']) > 0
            }
            
            pending_docs = validator.check_pending_documents(uploaded_docs, all_analyzed)
            conditional_docs = validator.check_conditional_documents(uploaded_docs, {}, all_emis)
            if conditional_docs:
                pending_docs['pending_documents'].extend(conditional_docs)
            
            form_data = validator.extract_form_data_from_documents(all_analyzed)
            for key, value in form_data.items():
                if key not in applicant_info or not applicant_info.get(key):
                    applicant_info[key] = value
            
            pending_forms = validator.check_pending_form_details(applicant_info)
            
            status_text.text("❓ Generating queries...")
            progress_bar.progress(95)
            
            analysis_summary = {
                'emis_found': all_emis,
                'salary_slips_count': len(categorized['salary_slips']),
                'job_since_years': 2,
                'average_bank_balance': bank_statement_data.get('average_balance', 0) if bank_statement_data else 0
            }
            
            queries = query_gen.generate_queries(
                analysis_summary,
                eligibility,
                pending_docs,
                pending_forms
            )
            
            formatted_queries = query_gen.format_queries_for_report(queries)
            
            status_text.text("✅ Analysis complete!")
            progress_bar.progress(100)
            
            st.session_state.analyzed_data = {
                'applicant_info': applicant_info,
                'salary_analysis': {'salary_slips': categorized['salary_slips']},
                'eligibility': eligibility,
                'obligations': eligibility['calculations'].get('emi_details', []),
                'pending_docs': pending_docs,
                'pending_forms': pending_forms,
                'queries': formatted_queries,
                'all_analyzed': all_analyzed,
                'categorized': categorized,
                'bank_statement_data': bank_statement_data
            }
            
            st.session_state.categorized_docs = categorized
            
            st.success(f"✅ Analyzed {total_files} documents successfully!")
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            with st.expander("Debug Info"):
                st.code(traceback.format_exc())


def recalculate_eligibility(requested_amount, interest_rate):
    """Recalculate loan eligibility with new parameters and excluded EMIs"""
    try:
        loan_calc = LoanEligibilityCalculator(config=st.session_state.loan_config)
        validator = DocumentValidator()
        query_gen = QueryGenerator()
        
        applicant_info = st.session_state.analyzed_data['applicant_info'].copy()
        applicant_info['loan_amount'] = requested_amount
        applicant_info['interest_rate'] = interest_rate
        
        salary_slips = st.session_state.analyzed_data['salary_analysis']['salary_slips']
        
        all_emis = []
        for obl in st.session_state.analyzed_data['obligations']:
            all_emis.append({
                'lender': obl['lender'],
                'emi_amount': obl['amount'],
                'loan_type': obl['type'],
                'has_loan_document': obl.get('has_loan_document', False)
            })
        
        auto_tenure = loan_calc.calculate_auto_tenure(applicant_info.get('current_age', 30))
        applicant_info['tenure'] = auto_tenure
        
        eligibility = loan_calc.calculate_eligibility(
            applicant_info,
            salary_slips,
            all_emis,
            requested_amount,
            None,
            interest_rate,
            st.session_state.excluded_emis
        )
        
        pending_docs = st.session_state.analyzed_data['pending_docs']
        pending_forms = st.session_state.analyzed_data['pending_forms']
        
        analysis_summary = {
            'emis_found': all_emis,
            'salary_slips_count': len(salary_slips),
            'job_since_years': 2,
            'average_bank_balance': st.session_state.analyzed_data.get('bank_statement_data', {}).get('average_balance', 0)
        }
        
        queries = query_gen.generate_queries(
            analysis_summary,
            eligibility,
            pending_docs,
            pending_forms
        )
        
        formatted_queries = query_gen.format_queries_for_report(queries)
        
        st.session_state.analyzed_data['eligibility'] = eligibility
        st.session_state.analyzed_data['applicant_info'] = applicant_info
        st.session_state.analyzed_data['obligations'] = eligibility['calculations'].get('emi_details', [])
        st.session_state.analyzed_data['queries'] = formatted_queries
        
    except Exception as e:
        st.error(f"❌ Recalculation error: {str(e)}")


def display_results(data):
    """Display comprehensive analysis results"""
    
    st.header("📊 Analysis Results")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Gross Monthly Income",
            f"₹{data['eligibility']['calculations'].get('gross_monthly_income', 0):,.0f}"
        )
    
    with col2:
        foir = data['eligibility']['calculations'].get('foir_with_requested_loan', 0)
        st.metric(
            "FOIR",
            f"{foir:.1f}%",
            delta=f"{foir - st.session_state.loan_config['foir_salaried']:.1f}%" if foir > st.session_state.loan_config['foir_salaried'] else "Within Limit",
            delta_color="inverse"
        )
    
    with col3:
        eligible = data['eligibility'].get('eligible')
        st.metric(
            "Status",
            "ELIGIBLE" if eligible else "NOT ELIGIBLE"
        )
    
    with col4:
        tenure = data['eligibility']['calculations'].get('approved_tenure_years', 'N/A')
        st.metric(
            "Tenure (Auto)",
            f"{tenure} years" if tenure != 'N/A' else 'N/A'
        )
    
    st.markdown("---")
    
    with st.expander("👤 APPLICANT DETAILS", expanded=True):
        info = data['applicant_info']
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {info.get('applicant_name', 'N/A')}")
            st.write(f"**PAN:** {info.get('pan_masked', 'N/A')}")
            st.write(f"**Aadhar:** {info.get('aadhar_masked', 'N/A')}")
            st.write(f"**Age:** {info.get('current_age', 'N/A')} years")
        
        with col2:
            st.write(f"**Employer:** {info.get('employer', 'N/A')}")
            st.write(f"**Designation:** {info.get('designation', 'N/A')}")
            st.write(f"**Department:** {info.get('department', 'N/A')}")
            st.write(f"**Loan Amount:** ₹{info.get('loan_amount', 0):,.0f}")
    
    with st.expander("💰 SALARY BREAKDOWN"):
      salary_slips = data['salary_analysis'].get('salary_slips', [])

      if salary_slips:
        import pandas as pd
        
        combined = []

        for slip in salary_slips:
            month = slip.get("month", "N/A")

            earnings = slip.get("earnings", {})
            deductions = slip.get("deductions", {})

            combined.append({
                "Month": month,
                "Basic": earnings.get("basic", 0),
                "HRA": earnings.get("hra", 0),
                "Special Allowance": earnings.get("special_allowance", 0),
                "Gross Salary": slip.get("gross_salary", 0),
                "Net Salary": slip.get("net_salary", 0)
            })

        df = pd.DataFrame(combined)
        st.dataframe(df, use_container_width=True)

      else:
        st.info("No salary slips found.")
    
    with st.expander("✅ ELIGIBILITY DETAILS", expanded=True):
        calc = data['eligibility']['calculations']
        eligible = data['eligibility'].get('eligible')
        
        if eligible:
            st.success("✓ ELIGIBLE FOR LOAN")
        else:
            st.error("✗ NOT ELIGIBLE")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current FOIR", f"{calc.get('current_foir_percent', 0):.2f}%")
            st.metric("FOIR with Loan", f"{calc.get('foir_with_requested_loan', 0):.2f}%")
        
        with col2:
            st.metric("Max Tenure", f"{calc.get('max_tenure_allowed', 'N/A')} years")
            st.metric("Remaining Service", f"{calc.get('remaining_service_years', 'N/A')} years")
        
        with col3:
            st.metric("EMI Required", f"₹{calc.get('emi_for_requested_loan', 0):,.2f}")
            st.metric("Max Loan by Income", f"₹{calc.get('max_loan_by_income', 0):,.2f}")
        
        if data['eligibility'].get('issues'):
            st.markdown("**Issues:**")
            for issue in data['eligibility']['issues']:
                st.warning(f"• {issue}")
    
    with st.expander("📋 EXISTING OBLIGATIONS"):
        if data['obligations']:
            for i, obl in enumerate(data['obligations']):
                col1, col2, col3 = st.columns([3, 2, 2])
                
                with col1:
                    st.write(f"**{obl['lender']}** ({obl['type'].title()})")
                
                with col2:
                    st.write(f"₹{obl['amount']:,.2f}/month")
                
                with col3:
                    if obl.get('excluded'):
                        st.success("Excluded")
                    else:
                        st.info("Active")
            
            total = sum(obl['amount'] for obl in data['obligations'] if not obl.get('excluded'))
            st.write(f"**Total Active: ₹{total:,.2f}**")
        else:
            st.info("No obligations found")
    
    with st.expander("📄 PENDING DOCUMENTS"):
        if data['pending_docs'].get('pending_documents'):
            for i, doc in enumerate(data['pending_docs']['pending_documents'], 1):
                st.write(f"{i}. {doc}")
        else:
            st.success("✓ All documents uploaded")
        
        st.progress(data['pending_docs'].get('completion_percentage', 0) / 100)
    
    with st.expander("❓ QUERIES"):
        if data['queries']:
            for query in data['queries']:
                st.write(query)
        else:
            st.success("✓ No queries")
    
    st.markdown("---")
    st.subheader("📥 Download Report")
    
    if st.button("Generate PDF Report", type="primary", use_container_width=True):
        with st.spinner("Generating PDF..."):
            try:
                report_gen = ReportGenerator()
                filename = f"loan_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                report_gen.generate_report(
                    data['applicant_info'],
                    data['salary_analysis'],
                    data['eligibility'],
                    data['obligations'],
                    data['pending_docs'],
                    data['pending_forms'],
                    data['queries'],
                    filename,
                    data.get('bank_statement_data')
                )
                
                with open(filename, 'rb') as f:
                    pdf_data = f.read()
                
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_data,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.success("✅ PDF generated!")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
