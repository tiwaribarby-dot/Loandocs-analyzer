class QueryGenerator:
    """Generate probable queries based on document analysis and historical patterns"""
    
    def __init__(self):
        # Common query categories from historical data
        self.QUERY_CATEGORIES = {
            'documents': 'Document Related Queries',
            'employment': 'Employment Verification',
            'obligations': 'Loan Obligations & Credit',
            'eligibility': 'Loan Eligibility',
            'property': 'Property Related',
            'ratios': 'Financial Ratios',
            'verification': 'Verification Queries'
        }
    
    def generate_queries(self, analysis_results, eligibility_results, pending_docs, pending_forms):
        """
        Generate probable queries based on analysis
        """
        queries = []
        
        # 1. Document-related queries
        if pending_docs.get('pending_documents'):
            for doc in pending_docs['pending_documents']:
                if 'Salary Slip' in doc:
                    queries.append({
                        'category': 'documents',
                        'query': f"SALARY SLIP - {doc}",
                        'priority': 'High'
                    })
                elif 'Form 16' in doc:
                    queries.append({
                        'category': 'documents',
                        'query': "FORM 16 - Latest Form 16 with Part A and Part B required",
                        'priority': 'High'
                    })
                elif 'Bank Statement' in doc:
                    queries.append({
                        'category': 'documents',
                        'query': "BANK STATEMENT - 6 months salary account bank statement required in PDF format",
                        'priority': 'High'
                    })
                else:
                    queries.append({
                        'category': 'documents',
                        'query': f"{doc.upper()} - Required for processing",
                        'priority': 'High'
                    })
        
        # 2. Employment verification queries
        job_since = analysis_results.get('job_since_years', 0)
        if job_since < 3:
            queries.append({
                'category': 'employment',
                'query': "APPOINTMENT LETTER - Required as current employment is less than 3 years",
                'priority': 'Medium'
            })
            queries.append({
                'category': 'employment',
                'query': "RESUME - Complete work history required",
                'priority': 'Medium'
            })
        
        # Check if office address is incomplete
        if pending_forms.get('pending_form_fields'):
            if any('Office Address' in field for field in pending_forms['pending_form_fields']):
                queries.append({
                    'category': 'employment',
                    'query': "EMPLOYER LETTER - Detailed office address required for verification",
                    'priority': 'High'
                })
        
        # 3. Obligation-related queries
        emis = analysis_results.get('emis_found', [])
        if len(emis) > 0:
            for emi in emis:
                loan_type = emi.get('loan_type') or 'Unknown'
                lender = emi.get('lender') or 'Unknown'
                amount = emi.get('emi_amount', 0)
                
                loan_type_display = loan_type.title() if loan_type != 'Unknown' else 'Unknown'
                
                queries.append({
                    'category': 'obligations',
                    'query': f"LOAN OUTSTANDING LETTER - {loan_type_display} loan with {lender}, EMI Rs{amount:,.0f} - Statement of Account required",
                    'priority': 'High'
                })
        
        # Check for credit card obligations
        if any(emi.get('loan_type') == 'credit card' for emi in emis):
            queries.append({
                'category': 'obligations',
                'query': "CREDIT CARD STATEMENT - Latest credit card statement required to verify outstanding and utilization",
                'priority': 'Medium'
            })
        
        # 4. Eligibility-related queries
        if not eligibility_results.get('eligible'):
            issues = eligibility_results.get('issues', [])
            
            for issue in issues:
                if 'FOIR' in issue:
                    foir = eligibility_results.get('calculations', {}).get('foir_with_requested_loan', 0)
                    queries.append({
                        'category': 'eligibility',
                        'query': f"LOAN ELIGIBILITY NOT AS PER NORMS - FOIR at {foir:.1f}% exceeds 60%. Loan amount may need to be reduced or existing loans closed.",
                        'priority': 'Critical'
                    })
                
                if 'age' in issue.lower():
                    queries.append({
                        'category': 'eligibility',
                        'query': "LOAN TERM NOT AS PER NORMS - Tenure exceeds maximum allowed based on applicant age. Confirmation required.",
                        'priority': 'High'
                    })
        
        # 5. Stretched ratios
        current_foir = eligibility_results.get('calculations', {}).get('current_foir_percent', 0)
        if current_foir > 40:
            queries.append({
                'category': 'ratios',
                'query': f"STRETCHED RATIOS NOT JUSTIFIED - Current FOIR at {current_foir:.1f}% indicates high existing obligations. Consider loan closure before disbursement.",
                'priority': 'High'
            })
        
        # Check if income is too low
        gross_income = eligibility_results.get('calculations', {}).get('gross_monthly_income', 0)
        if gross_income < 25000:
            queries.append({
                'category': 'eligibility',
                'query': f"OTHER INCOME PROOF - Gross monthly income (Rs{gross_income:,.0f}) is below minimum threshold. Additional income proof may be required.",
                'priority': 'Medium'
            })
        
        # 6. Form field queries
        critical_fields = ['Mobile Number', 'Email ID', 'Current Address', 'Office Address']
        for field in pending_forms.get('pending_form_fields', []):
            if any(cf in field for cf in critical_fields):
                queries.append({
                    'category': 'verification',
                    'query': f"FORM DETAILS INCOMPLETE - {field} required for processing",
                    'priority': 'High'
                })
        
        # 7. Property-related queries
        if 'Property Address' in pending_forms.get('pending_form_fields', []):
            queries.append({
                'category': 'property',
                'query': "PROPERTY - COST BREAK UP SHEET - Property details and cost breakup required",
                'priority': 'Medium'
            })
        
        # 8. Reference queries
        if any('Reference' in field for field in pending_forms.get('pending_form_fields', [])):
            queries.append({
                'category': 'verification',
                'query': "REFERENCE DETAILS - Complete details of both references required (Name, Mobile, Email, Address)",
                'priority': 'Low'
            })
        
        # 9. Banking-related queries
        avg_balance = analysis_results.get('average_bank_balance')
        try:
           avg_balance = float(avg_balance or 0)
        except (TypeError, ValueError):
           avg_balance = 0
        if avg_balance < 10000:
            queries.append({
                'category': 'ratios',
                'query': f"BANK BALANCES NOT AS PER NORMS - Low average balance (Rs{avg_balance:,.0f}) observed. Better banking required.",
                'priority': 'Medium'
            })
        
        # 10. Salary breakup query
        if analysis_results.get('salary_slips_count', 0) < 3:
            months_needed = 3 - analysis_results.get('salary_slips_count', 0)
            queries.append({
                'category': 'documents',
                'query': f"SALARY SLIP - {months_needed} additional month(s) salary slip required (total 3 months needed)",
                'priority': 'High'
            })
        
        # Sort queries by priority
        priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        queries.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return queries
    
    def format_queries_for_report(self, queries):
        """Format queries in a structured way for the report"""
        if not queries:
            return "No queries identified. File appears complete for processing."
        
        formatted = []
        for i, query in enumerate(queries, 1):
            formatted.append(f"{i}. {query['query']}")
        
        return formatted
    
    def generate_recommendations(self, eligibility_results):
        """Generate recommendations based on eligibility analysis"""
        recommendations = []
        
        if eligibility_results.get('eligible'):
            recommendations.append("APPROVED: Application meets eligibility criteria")
            recommended_amount = eligibility_results.get('calculations', {}).get('approved_loan_amount', 0)
            if recommended_amount:
                recommendations.append(f"APPROVED: Recommended loan amount: Rs{recommended_amount:,.0f}")
        else:
            max_possible = eligibility_results.get('calculations', {}).get('recommended_loan_amount', 0)
            if max_possible:
                recommendations.append(f"WARNING: Maximum possible loan amount: Rs{max_possible:,.0f}")
            
            recommendations.append("WARNING: Consider the following to improve eligibility:")
            
            # Specific recommendations
            current_foir = eligibility_results.get('calculations', {}).get('current_foir_percent', 0)
            if current_foir > 40:
                recommendations.append("  - Close or reduce existing loan obligations")
            
            issues = eligibility_results.get('issues', [])
            if any('tenure' in issue.lower() for issue in issues):
                recommendations.append("  - Reduce loan tenure to match age eligibility")
            
            if any('foir' in issue.lower() for issue in issues):
                recommendations.append("  - Reduce requested loan amount to meet FOIR norms")
        
        return recommendations
