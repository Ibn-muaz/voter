"""
Fake data generator for testing the INEC Underage Eradicator system.

Generates realistic Nigerian voter registration data with controlled underage percentages.
"""

import random
import uuid
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from faker import Faker
from django.utils import timezone

from apps.registration.models import VoterRegistration
from apps.utils.models import NigerianState, LocalGovernmentArea, Occupation


class FakeDataGenerator:
    """
    Generates fake voter registration data for testing.
    """

    def __init__(self):
        self.faker = Faker('en_NG')  # Nigerian English locale
        self.states_data = self._load_nigerian_states()
        self.occupations = [
            'Teacher', 'Doctor', 'Engineer', 'Farmer', 'Trader', 'Student',
            'Civil Servant', 'Business Owner', 'Driver', 'Nurse', 'Lawyer',
            'Accountant', 'Mechanic', 'Tailor', 'Carpenter', 'Unemployed'
        ]

    def _load_nigerian_states(self) -> Dict[str, List[str]]:
        """Load Nigerian states and their LGAs."""
        return {
            'Lagos': [
                'Agege', 'Ajeromi-Ifelodun', 'Alimosho', 'Amuwo-Odofin', 'Apapa',
                'Badagry', 'Epe', 'Eti-Osa', 'Ibeju-Lekki', 'Ifako-Ijaiye',
                'Ikeja', 'Ikorodu', 'Kosofe', 'Lagos Island', 'Lagos Mainland',
                'Mushin', 'Ojo', 'Oshodi-Isolo', 'Shomolu', 'Surulere'
            ],
            'Abuja': [
                'Abaji', 'Abuja Municipal', 'Bwari', 'Gwagwalada', 'Kuje', 'Kwali'
            ],
            'Kano': [
                'Ajingi', 'Albasu', 'Bagwai', 'Bebeji', 'Bichi', 'Bunkure',
                'Dala', 'Dambatta', 'Dawakin Kudu', 'Dawakin Tofa', 'Doguwa',
                'Fagge', 'Gabasawa', 'Garko', 'Garun Mallam', 'Gaya', 'Gezawa',
                'Gwale', 'Gwarzo', 'Kabo', 'Kano Municipal', 'Karaye', 'Kibiya',
                'Kiru', 'Kumbotso', 'Kura', 'Madobi', 'Makoda', 'Minjibir',
                'Nasarawa', 'Rano', 'Rimin Gado', 'Rogo', 'Shanono', 'Sumaila',
                'Takai', 'Tarauni', 'Tofa', 'Tsanyawa', 'Tudun Wada', 'Ungogo',
                'Warawa', 'Wudil'
            ],
            'Rivers': [
                'Abua/Odual', 'Ahoada East', 'Ahoada West', 'Akuku-Toru', 'Andoni',
                'Asari-Toru', 'Bonny', 'Degema', 'Eleme', 'Emuoha', 'Etche',
                'Gokana', 'Ikwerre', 'Khana', 'Obio/Akpor', 'Ogba/Egbema/Ndoni',
                'Ogu/Bolo', 'Okrika', 'Omuma', 'Opobo/Nkoro', 'Oyigbo', 'Port Harcourt',
                'Tai'
            ],
            'Oyo': [
                'Afijio', 'Akinyele', 'Atiba', 'Atisbo', 'Egbeda', 'Ibadan North',
                'Ibadan North-East', 'Ibadan North-West', 'Ibadan South-East',
                'Ibadan South-West', 'Ibarapa Central', 'Ibarapa East', 'Ibarapa North',
                'Ido', 'Irepo', 'Iseyin', 'Itesiwaju', 'Iwajowa', 'Kajola', 'Lagelu',
                'Ogbomosho North', 'Ogbomosho South', 'Ogo Oluwa', 'Olorunsogo',
                'Oluyole', 'Ona Ara', 'Orelope', 'Ori Ire', 'Oyo East', 'Oyo West',
                'Saki East', 'Saki West', 'Surulere'
            ]
        }

    def generate_registrations(self, count: int, underage_percentage: float = 0.3) -> List[VoterRegistration]:
        """
        Generate fake voter registrations.

        Args:
            count: Number of registrations to generate
            underage_percentage: Percentage of registrations that should be underage (0-1)

        Returns:
            List of created VoterRegistration objects
        """
        registrations = []
        underage_count = int(count * underage_percentage)
        adult_count = count - underage_count

        # Generate adult registrations
        for _ in range(adult_count):
            reg = self._generate_single_registration(adult=True)
            registrations.append(reg)

        # Generate underage registrations
        for _ in range(underage_count):
            reg = self._generate_single_registration(adult=False)
            registrations.append(reg)

        # Shuffle to randomize order
        random.shuffle(registrations)

        return registrations

    def _generate_single_registration(self, adult: bool = True) -> VoterRegistration:
        """Generate a single fake registration."""
        # Select random state and LGA
        state_name = random.choice(list(self.states_data.keys()))
        lga_name = random.choice(self.states_data[state_name])

        # Generate personal information
        gender = random.choice(['male', 'female'])

        if gender == 'male':
            first_name = self.faker.first_name_male()
        else:
            first_name = self.faker.first_name_female()

        surname = self.faker.last_name()
        middle_name = self.faker.first_name()

        # Generate date of birth
        today = date.today()
        if adult:
            # Adults: 18-65 years old
            age = random.randint(18, 65)
        else:
            # Underage: 10-17 years old
            age = random.randint(10, 17)

        birth_year = today.year - age
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)  # Avoid invalid dates
        date_of_birth = date(birth_year, birth_month, birth_day)

        # Generate registration
        registration = VoterRegistration(
            surname=surname,
            first_name=first_name,
            middle_name=middle_name,
            date_of_birth=date_of_birth,
            gender=gender,
            occupation=random.choice(self.occupations),
            phone_number=self.faker.phone_number(),
            state_of_origin=state_name,
            lga_of_origin=lga_name,
            ward=self.faker.city_suffix() + " Ward",
            polling_unit=f"Polling Unit {random.randint(1, 50)}",
            residence_state=state_name,  # Same as origin for simplicity
            residence_lga=lga_name,
            residence_address=self.faker.address(),
            status='approved',  # Mark as approved for testing
            ai_verification_score=random.uniform(0.7, 1.0),
            age_verification_passed=adult,
            document_verification_passed=random.choice([True, True, False]),  # 66% pass rate
            biometric_verification_passed=random.choice([True, True, False]),
            anomaly_detection_passed=random.choice([True, False]),  # 50% pass rate
        )

        # Generate VIN
        registration.vin = self._generate_fake_vin()
        registration.approved_at = timezone.now() - timedelta(days=random.randint(1, 365))

        return registration

    def _generate_fake_vin(self) -> str:
        """Generate a fake Voter Identification Number."""
        return f"NG{random.randint(100000000, 999999999)}"

    def generate_bulk_data(self, total_registrations: int = 10000, underage_percentage: float = 0.3):
        """
        Generate and save bulk fake data to database.

        Args:
            total_registrations: Total number of registrations to create
            underage_percentage: Percentage of underage registrations
        """
        print(f"Generating {total_registrations} fake registrations with {underage_percentage*100}% underage...")

        registrations = self.generate_registrations(total_registrations, underage_percentage)

        # Bulk create
        created_regs = []
        batch_size = 1000

        for i in range(0, len(registrations), batch_size):
            batch = registrations[i:i+batch_size]
            VoterRegistration.objects.bulk_create(batch)
            created_regs.extend(batch)
            print(f"Created {len(created_regs)}/{total_registrations} registrations...")

        print("Fake data generation completed!")

        # Print statistics
        adults = sum(1 for r in created_regs if r.calculate_age() >= 18)
        underage = len(created_regs) - adults

        print(f"Adults: {adults} ({adults/len(created_regs)*100:.1f}%)")
        print(f"Underage: {underage} ({underage/len(created_regs)*100:.1f}%)")

        return created_regs

    def generate_test_scenarios(self) -> List[VoterRegistration]:
        """
        Generate specific test scenarios for AI testing.

        Returns:
            List of registrations with known characteristics
        """
        scenarios = []

        # Scenario 1: Obvious underage (16 year old)
        reg1 = VoterRegistration(
            surname="Young", first_name="Too", middle_name="Much",
            date_of_birth=date.today() - timedelta(days=16*365),
            gender='male', occupation='Student',
            state_of_origin='Lagos', lga_of_origin='Ikeja',
            residence_state='Lagos', residence_lga='Ikeja',
            residence_address='123 Test Street',
            status='pending_verification'
        )
        scenarios.append(reg1)

        # Scenario 2: Borderline age (17 years 11 months)
        reg2 = VoterRegistration(
            surname="Almost", first_name="Adult", middle_name="Now",
            date_of_birth=date.today() - timedelta(days=17*365 + 330),  # 17y 11m
            gender='female', occupation='Student',
            state_of_origin='Abuja', lga_of_origin='Abuja Municipal',
            residence_state='Abuja', residence_lga='Abuja Municipal',
            residence_address='456 Borderline Ave',
            status='pending_verification'
        )
        scenarios.append(reg2)

        # Scenario 3: Adult with suspicious data
        reg3 = VoterRegistration(
            surname="Suspicious", first_name="Adult", middle_name="Data",
            date_of_birth=date.today() - timedelta(days=25*365),
            gender='male', occupation='Student',  # Adult claiming to be student
            state_of_origin='Kano', lga_of_origin='Kano Municipal',
            residence_state='Kano', residence_lga='Kano Municipal',
            residence_address='789 Suspicious St',
            status='pending_verification'
        )
        scenarios.append(reg3)

        # Scenario 4: Valid adult
        reg4 = VoterRegistration(
            surname="Valid", first_name="Adult", middle_name="Registration",
            date_of_birth=date.today() - timedelta(days=30*365),
            gender='female', occupation='Teacher',
            state_of_origin='Rivers', lga_of_origin='Port Harcourt',
            residence_state='Rivers', residence_lga='Port Harcourt',
            residence_address='101 Valid Lane',
            status='pending_verification'
        )
        scenarios.append(reg4)

        return scenarios

    def populate_reference_data(self):
        """
        Populate reference data (states, LGAs, occupations).
        """
        print("Populating reference data...")

        # States and LGAs
        for state_name, lgas in self.states_data.items():
            state, created = NigerianState.objects.get_or_create(
                name=state_name,
                defaults={'code': state_name[:3].upper(), 'capital': f"{state_name} City"}
            )

            for lga_name in lgas:
                LocalGovernmentArea.objects.get_or_create(
                    name=lga_name,
                    state=state,
                    defaults={'code': f"{state_name[:2].upper()}{random.randint(100, 999)}"}
                )

        # Occupations
        for occupation_name in self.occupations:
            category = self._categorize_occupation(occupation_name)
            Occupation.objects.get_or_create(
                name=occupation_name,
                defaults={'category': category}
            )

        print("Reference data populated!")

    def _categorize_occupation(self, occupation: str) -> str:
        """Categorize occupation."""
        if occupation in ['Teacher', 'Doctor', 'Engineer', 'Nurse', 'Lawyer', 'Accountant']:
            return 'professional'
        elif occupation in ['Farmer', 'Trader', 'Business Owner']:
            return 'business'
        elif occupation in ['Driver', 'Mechanic', 'Tailor', 'Carpenter']:
            return 'skilled'
        elif occupation == 'Student':
            return 'student'
        elif occupation == 'Unemployed':
            return 'unemployed'
        elif occupation == 'Civil Servant':
            return 'professional'
        else:
            return 'other'


# Utility functions
def generate_fake_data(count: int = 1000, underage_pct: float = 0.3):
    """
    Convenience function to generate fake data.
    """
    generator = FakeDataGenerator()
    return generator.generate_bulk_data(count, underage_pct)


def generate_test_cases():
    """
    Generate test scenarios.
    """
    generator = FakeDataGenerator()
    scenarios = generator.generate_test_scenarios()

    # Save to database
    for reg in scenarios:
        reg.save()

    print(f"Generated {len(scenarios)} test scenarios")
    return scenarios


if __name__ == '__main__':
    # Example usage
    generator = FakeDataGenerator()
    generator.populate_reference_data()
    generator.generate_bulk_data(1000, 0.3)