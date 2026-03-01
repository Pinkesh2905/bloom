import os
import django
import random
import shutil
from django.utils import timezone
from django.core.files import File

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bloom.settings')
django.setup()

from django.contrib.auth.models import User
from therapists.models import TherapistProfile, Appointment, TherapistReview, TherapistSchedule
from django.conf import settings
from datetime import time

def seed_therapists():
    print("Clearing existing therapist data...")
    # Delete appointments and reviews first due to FK constraints
    TherapistReview.objects.all().delete()
    Appointment.objects.all().delete()
    
    # Identify and delete therapist users
    therapist_users = User.objects.filter(therapist_profile__isnull=False)
    therapist_users.delete()
    TherapistProfile.objects.all().delete()
    
    # Ensure media directories exist
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'therapist_pics'), exist_ok=True)
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'therapist_featured'), exist_ok=True)

    therapists_data = [
        {
            'username': 'dr_elara_vance',
            'first_name': 'Elara',
            'last_name': 'Vance',
            'email': 'elara.vance@bloom.io',
            'bio': 'Dr. Elara Vance is a pioneer in Neuro-Bloom therapy, blending traditional CBT with high-tech mindfulness interventions. With over 15 years of experience, she specializes in high-performance anxiety and digital burnout. Her approach is data-driven yet deeply empathetic, ensuring a tailored path to cognitive resonance.',
            'specializations': ['CBT', 'MINDFULNESS', 'ANXIETY'],
            'qualifications': ['PHD'],
            'languages': ['EN', 'FR'],
            'rate': 180.00,
            'years': 15,
            'social': {'linkedin': 'https://linkedin.com/elara-vance', 'twitter': '@elarav_bloom'},
            'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'profile_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_elara_vance_profile_1772288026777.png',
            'featured_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_elara_vance_featured_1772288043725.png'
        },
        {
            'username': 'dr_kai_chen',
            'first_name': 'Kai',
            'last_name': 'Chen',
            'email': 'kai.chen@bloom.io',
            'bio': 'Dr. Kai Chen focuses on Somatic Resilience and Trauma recovery. He believes the body carries stories the mind often forgets. Utilizing advanced somatic techniques and EMDR, Dr. Chen helps clients rewire their nervous systems for stability in an increasingly chaotic world.',
            'specializations': ['SOMATIC', 'EMDR', 'TRAUMA'],
            'qualifications': ['PSYD', 'LCSW'],
            'languages': ['EN', 'ZH', 'JA'],
            'rate': 165.00,
            'years': 12,
            'social': {'linkedin': 'https://linkedin.com/kai-chen-psych'},
            'video_url': '',
            'profile_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_kai_chen_profile_1772288061537.png',
            'featured_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_kai_chen_featured_1772288078016.png'
        },
        {
            'username': 'dr_maya_sharma',
            'first_name': 'Maya',
            'last_name': 'Sharma',
            'email': 'maya.sharma@bloom.io',
            'bio': 'Maya Sharma specializes in Adolescent Psychology and Family Systems. In the age of social media, she provides a grounded perspective for Gen Z and Alpha, helping families navigate the complexities of digital identity and emotional regulation.',
            'specializations': ['ADOLESCENT', 'FAMILY_THERAPY', 'DEPRESSION'],
            'qualifications': ['MSW', 'LMFT'],
            'languages': ['EN', 'HI'],
            'rate': 140.00,
            'years': 8,
            'social': {'twitter': '@drmayasharma'},
            'video_url': '',
            'profile_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_maya_sharma_profile_1772288098774.png',
            'featured_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_maya_sharma_featured_1772288116656.png'
        },
        {
            'username': 'dr_julian_ross',
            'first_name': 'Julian',
            'last_name': 'Ross',
            'email': 'julian.ross@bloom.io',
            'bio': 'Dr. Julian Ross is a specialist in Addiction recovery and Grief counseling. His "Resurrection Method" focuses on rebuilding core identity after profound loss or dependency. He offers a safe, non-judgmental space for raw emotional processing.',
            'specializations': ['ADDICTION', 'GRIEF', 'GROUP_THERAPY'],
            'qualifications': ['PHD', 'LPC'],
            'languages': ['EN', 'ES'],
            'rate': 155.00,
            'years': 20,
            'social': {'linkedin': 'https://linkedin.com/julian-ross-recovery'},
            'video_url': '',
            'profile_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_julian_ross_profile_1772288137041.png',
            'featured_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_julian_ross_featured_1772288153358.png'
        },
        {
            'username': 'dr_sofia_ricci',
            'first_name': 'Sofia',
            'last_name': 'Ricci',
            'email': 'sofia.ricci@bloom.io',
            'bio': 'Dr. Sofia Ricci explores the intersection of Art Therapy and Psychodynamic theory. She helps clients express the inexpressible through creative flow, unlocking subconscious blocks and fostering a deeper sense of self-actualization.',
            'specializations': ['ART_THERAPY', 'PSYCHODYNAMIC', 'HUMANISTIC'],
            'qualifications': ['MA_PSYCHOLOGY', 'LPC'],
            'languages': ['IT', 'EN', 'ES'],
            'rate': 130.00,
            'years': 10,
            'social': {'instagram': '@sofia_ricci_art_therapy'},
            'video_url': '',
            'profile_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_sofia_ricci_profile_1772288169759.png',
            'featured_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_sofia_ricci_featured_1772288188493.png'
        },
        {
            'username': 'dr_marcus_thorne',
            'first_name': 'Marcus',
            'last_name': 'Thorne',
            'email': 'marcus.thorne@bloom.io',
            'bio': 'Dr. Marcus Thorne is a specialist in Geriatric Psychology and Life Transitions. He provides vital support for the aging population and their caregivers, focusing on cognitive health and the search for meaning in the later chapters of life.',
            'specializations': ['GERIATRIC', 'MINDFULNESS', 'HUMANISTIC'],
            'qualifications': ['PHD', 'LPCC'],
            'languages': ['EN', 'DE'],
            'rate': 175.00,
            'years': 25,
            'social': {'linkedin': 'https://linkedin.com/marcus-thorne-geriatrics'},
            'video_url': '',
            'profile_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_marcus_thorne_profile_1772288206950.png',
            'featured_img': r'C:\Users\pinke\.gemini\antigravity\brain\ac0ee7f5-f3eb-4722-a734-7845794a9264\dr_marcus_thorne_featured_1772288351678.png'
        }
    ]

    for data in therapists_data:
        print(f"Creating therapist: {data['username']}...")
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password='password123',
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        
        profile = TherapistProfile.objects.create(
            user=user,
            license_number=f"LIC-{random.randint(10000, 99999)}",
            specializations=data['specializations'],
            qualifications=data['qualifications'],
            languages_spoken=data['languages'],
            bio=data['bio'],
            years_experience=data['years'],
            hourly_rate=data['rate'],
            social_links=data['social'],
            video_intro_url=data['video_url'],
            is_verified=True,
            is_approved=True,
            license_verified=True,
            background_check_completed=True,
            rating=random.uniform(4.5, 5.0), # Higher rating for new therapists
            total_reviews=random.randint(20, 100),
            total_sessions=random.randint(200, 800),
            profile_complete=True,
            onboarding_completed=True,
            response_time_hours=random.randint(1, 4)
        )
        
        # Handle Profile Picture
        if os.path.exists(data['profile_img']):
            with open(data['profile_img'], 'rb') as f:
                profile.profile_picture.save(f"{data['username']}_profile.png", File(f), save=True)
        
        # Handle Featured Image
        if os.path.exists(data['featured_img']):
            with open(data['featured_img'], 'rb') as f:
                profile.featured_image.save(f"{data['username']}_featured.png", File(f), save=True)
        
        # Create TherapistSchedule entries
        for day in range(5): # Mon-Fri
            start_hour = random.choice([9, 13])
            end_hour = start_hour + random.choice([3, 4]) # 3 or 4 hour blocks
            
            TherapistSchedule.objects.create(
                therapist=profile,
                day_of_week=day,
                start_time=time(start_hour, 0, 0),
                end_time=time(end_hour, 0, 0)
            )

    print("Seeding complete with images!")

if __name__ == "__main__":
    seed_therapists()
