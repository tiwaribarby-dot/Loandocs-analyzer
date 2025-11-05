import datetime
from datetime import datetime as dt

class LoanEligibilityCalculator:
    def __init__(self, config=None):
        if config is None:
            config = {}
        
        foir_salaried = config.get('foir_salaried', 60)
        self.FOIR_SALARIED = foir_salaried / 100 if foir_salaried > 1 else foir_salaried
        
        self.MAX_AGE_SALARIED = config.get('max_age_salaried', 60)
        self.MAX_TENURE_YEARS = config.get('max_tenure_years', 30)
        self.MIN_INCOME_THRESHOLD = config.get('min_income_threshold', 25000)
        
        high_foir = config.get('high_foir_threshold', 40)
        self.HIGH_FOIR_THRESHOLD = high_foir / 100 if high_foir > 1 else high_foir
        
        foir_self = config.get('foir_self_employed', 90)
        self.FOIR_SELF_EMPLOYED_MAX = foir_self / 100 if foir_self > 1 else foir_self
        
        self.MAX_AGE_SELF_EMPLOYED = config.get('max_age_self_employed', 70)
    
    def update_config(self, config):
        """Update loan calculation parameters dynamically"""
        if 'foir_salaried' in config:
            self.FOIR_SALARIED = config['foir_salaried'] / 100 if config['foir_salaried'] > 1 else config['foir_salaried']
        if 'max_age_salaried' in config:
            self.MAX_AGE_SALARIED = config['max_age_salaried']
        if 'max_tenure_years' in config:
            self.MAX_TENURE_YEARS = config['max_tenure_years']
        if 'min_income_threshold' in config:
            self.MIN_INCOME_THRESHOLD = config['min_income_threshold']
        if 'high_foir_threshold' in config:
            self.HIGH_FOIR_THRESHOLD = config['high_foir_threshold'] / 100 if config['high_foir_threshold'] > 1 else config['high_foir_threshold']
        if 'foir_self_employed' in config:
            self.FOIR_SELF_EMPLOYED_MAX = config['foir_self_employed'] / 100 if config['foir_self_employed'] > 1 else config['foir_self_employed']
    
    def calculate_age(self, date_of_birth):
        """Calculate age from date of birth"""
        try:
            if isinstance(date_of_birth, str):
                for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y"]:
                    try:
                        dob = dt.strptime(date_of_birth, fmt)
                        break
                    except:
                        continue
                else:
                    return None
            else:
                dob = date_of_birth
            
            today = dt.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        except:
            return None
    
    def calculate_remaining_service_years(self, current_age, max_age=None):
        """Calculate remaining years until retirement"""
        if current_age is None:
            return None
        if max_age is None:
            max_age = self.MAX_AGE_SALARIED
        return max(0, max_age - current_age)
    
    def calculate_auto_tenure(self, current_age):
        """Auto-calculate maximum possible tenure based on age"""
        remaining_years = self.calculate_remaining_service_years(current_age)
        if remaining_years is None:
            return self.MAX_TENURE_YEARS
        return min(self.MAX_TENURE_YEARS, remaining_years)
    
    def categorize_salary_components(self, salary_slip):
        """Categorize all salary components into fixed and variable"""
        earnings = salary_slip.get('earnings', {})
        
        fixed_components = {
            'basic': earnings.get('basic', 0),
            'hra': earnings.get('hra', 0),
            'conveyance_allowance': earnings.get('conveyance_allowance', 0),
            'travel_allowance': earnings.get('travel_allowance', 0),
            'medical_allowance': earnings.get('medical_allowance', 0),
            'special_allowance': earnings.get('special_allowance', 0),
            'lta': earnings.get('lta', 0),
            'city_compensatory_allowance': earnings.get('city_compensatory_allowance', 0),
            'education_allowance': earnings.get('education_allowance', 0),
            'other_allowances': earnings.get('other_allowances', 0)
        }
        
        variable_components = {
            'incentive': earnings.get('incentive', 0),
            'overtime': earnings.get('overtime', 0),
            'bonus': earnings.get('bonus', 0),
            'commission': earnings.get('commission', 0),
            'arrears': earnings.get('arrears', 0)
        }
        
        return fixed_components, variable_components
    
    def calculate_gross_monthly_income(self, salary_slips):
        """
        Calculate gross monthly income from salary slips
        Fixed: 100% of fixed components
        Variable: 50% of average of last 6 months (or available months / 6)
        """
        if not salary_slips or len(salary_slips) == 0:
            return 0, 0, 0, {}
        
        total_fixed = 0
        total_variable = 0
        count = len(salary_slips)
        
        detailed_fixed = {}
        detailed_variable = {}
        
        for slip in salary_slips:
            fixed, variable = self.categorize_salary_components(slip)
            
            slip_fixed_total = sum(fixed.values())
            slip_variable_total = sum(variable.values())
            
            total_fixed += slip_fixed_total
            total_variable += slip_variable_total
            
            for key, value in fixed.items():
                detailed_fixed[key] = detailed_fixed.get(key, 0) + value
            for key, value in variable.items():
                detailed_variable[key] = detailed_variable.get(key, 0) + value
        
        avg_fixed = total_fixed / count
        avg_variable_considerable = (total_variable / 6) * 0.5
        gross_monthly = avg_fixed + avg_variable_considerable
        
        avg_detailed_fixed = {k: v / count for k, v in detailed_fixed.items()}
        avg_detailed_variable = {k: (v / 6) * 0.5 for k, v in detailed_variable.items()}
        
        return gross_monthly, avg_fixed, avg_variable_considerable, {
            'fixed_breakdown': avg_detailed_fixed,
            'variable_breakdown': avg_detailed_variable
        }
    
    def calculate_total_obligations(self, emis_list, excluded_emis=None):
        """Calculate total monthly obligations (EMIs only, with exclusion support)"""
        if excluded_emis is None:
            excluded_emis = []
        
        total = 0
        emi_details = []
        
        for i, emi in enumerate(emis_list):
            amount = emi.get('emi_amount', 0)
            is_excluded = i in excluded_emis
            
            if not is_excluded:
                total += amount
            
            emi_details.append({
                'lender': emi.get('lender', 'Unknown'),
                'amount': amount,
                'type': emi.get('loan_type', 'Unknown'),
                'excluded': is_excluded,
                'has_loan_document': emi.get('has_loan_document', False)
            })
        
        return total, emi_details
    
    def calculate_foir(self, total_obligations, gross_income):
        """Calculate Fixed Obligation to Income Ratio (FOIR)"""
        if gross_income == 0:
            return 0
        return (total_obligations / gross_income) * 100
    
    def calculate_maximum_emi(self, gross_income, existing_obligations):
        """Calculate maximum EMI allowed based on FOIR"""
        max_total_obligation = gross_income * self.FOIR_SALARIED
        max_new_emi = max_total_obligation - existing_obligations
        return max(0, max_new_emi)
    
    def calculate_loan_amount_from_emi(self, emi, interest_rate, tenure_months):
        """Calculate loan amount from EMI using standard formula"""
        if interest_rate == 0:
            return emi * tenure_months
        
        monthly_rate = interest_rate / (12 * 100)
        denominator = monthly_rate * ((1 + monthly_rate) ** tenure_months)
        numerator = ((1 + monthly_rate) ** tenure_months) - 1
        
        if denominator == 0:
            return 0
        
        loan_amount = emi * (numerator / denominator)
        return loan_amount
    
    def calculate_eligibility(self, applicant_data, salary_slips, emis_list, 
                            requested_loan_amount, requested_tenure_years=None,
                            interest_rate=8.5, excluded_emis=None):
        """
        Main function to calculate loan eligibility
        Auto-calculates tenure if not provided
        Returns detailed eligibility report
        """
        result = {
            'eligible': False,
            'issues': [],
            'warnings': [],
            'calculations': {}
        }
        
        age = self.calculate_age(applicant_data.get('date_of_birth'))
        if age is None:
            result['issues'].append("Unable to determine applicant age from date of birth")
            age = applicant_data.get('age', 30)
        
        result['calculations']['current_age'] = age
        
        if age >= self.MAX_AGE_SALARIED:
            result['issues'].append(f"Applicant age ({age}) exceeds maximum age limit ({self.MAX_AGE_SALARIED})")
        
        remaining_years = self.calculate_remaining_service_years(age, self.MAX_AGE_SALARIED)
        result['calculations']['remaining_service_years'] = remaining_years
        
        max_tenure = min(self.MAX_TENURE_YEARS, remaining_years)
        result['calculations']['max_tenure_allowed'] = max_tenure
        
        if requested_tenure_years is None:
            requested_tenure_years = max_tenure
        
        if requested_tenure_years > max_tenure:
            result['issues'].append(
                f"Requested tenure ({requested_tenure_years} years) exceeds maximum allowed "
                f"({max_tenure} years based on age {age})"
            )
            requested_tenure_years = max_tenure
        
        result['calculations']['approved_tenure_years'] = requested_tenure_years
        
        gross_income, fixed_income, variable_income, breakdowns = self.calculate_gross_monthly_income(salary_slips)
        result['calculations']['gross_monthly_income'] = round(gross_income, 2)
        result['calculations']['fixed_income'] = round(fixed_income, 2)
        result['calculations']['variable_income_considered'] = round(variable_income, 2)
        result['calculations']['income_breakdowns'] = breakdowns
        
        total_obligations, emi_details = self.calculate_total_obligations(emis_list, excluded_emis)
        result['calculations']['total_existing_obligations'] = round(total_obligations, 2)
        result['calculations']['emi_details'] = emi_details
        
        current_foir = self.calculate_foir(total_obligations, gross_income)
        result['calculations']['current_foir_percent'] = round(current_foir, 2)
        
        max_emi = self.calculate_maximum_emi(gross_income, total_obligations)
        result['calculations']['max_emi_allowed'] = round(max_emi, 2)
        
        tenure_months = requested_tenure_years * 12
        max_loan_by_income = self.calculate_loan_amount_from_emi(max_emi, interest_rate, tenure_months)
        result['calculations']['max_loan_by_income'] = round(max_loan_by_income, 2)
        
        if interest_rate > 0:
            monthly_rate = interest_rate / (12 * 100)
            emi_for_requested = (requested_loan_amount * monthly_rate * 
                                ((1 + monthly_rate) ** tenure_months)) / \
                               (((1 + monthly_rate) ** tenure_months) - 1)
        else:
            emi_for_requested = requested_loan_amount / tenure_months
        
        result['calculations']['emi_for_requested_loan'] = round(emi_for_requested, 2)
        
        total_emi_with_loan = total_obligations + emi_for_requested
        foir_with_loan = self.calculate_foir(total_emi_with_loan, gross_income)
        result['calculations']['foir_with_requested_loan'] = round(foir_with_loan, 2)
        
        if foir_with_loan <= (self.FOIR_SALARIED * 100):
            if age < self.MAX_AGE_SALARIED and requested_tenure_years <= max_tenure:
                result['eligible'] = True
                result['calculations']['approved_loan_amount'] = requested_loan_amount
            else:
                result['warnings'].append("Loan may be approved with conditions")
                result['calculations']['approved_loan_amount'] = min(requested_loan_amount, max_loan_by_income)
        else:
            result['issues'].append(
                f"FOIR ({round(foir_with_loan, 2)}%) exceeds maximum allowed ({self.FOIR_SALARIED * 100}%)"
            )
            result['calculations']['recommended_loan_amount'] = round(max_loan_by_income, 2)
        
        if gross_income < self.MIN_INCOME_THRESHOLD:
            result['warnings'].append(f"Gross income is below typical minimum threshold (Rs{self.MIN_INCOME_THRESHOLD:,.0f})")
        
        if current_foir > (self.HIGH_FOIR_THRESHOLD * 100):
            result['warnings'].append(f"High existing obligations (FOIR: {round(current_foir, 2)}%)")
        
        return result
