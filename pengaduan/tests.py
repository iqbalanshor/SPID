import io
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from pengaduan.models import CustomUser, Pengaduan

class SPIDTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a test user
        self.user = CustomUser.objects.create_user(
            username='budi',
            email='budi@gmail.com',
            password='testpassword123',
            nama_lengkap='Budi Cahyono',
            nomor_hp='081234567890'
        )
        # Create a test staff admin
        self.admin = CustomUser.objects.create_user(
            username='admin_test',
            email='admin@spid.gov',
            password='adminpassword123',
            nama_lengkap='Admin SPID',
            nomor_hp='089876543210',
            is_staff=True,
            is_superuser=True
        )

    def test_anonymous_redirect(self):
        """Test that unauthenticated users are redirected to login page for protected views."""
        protected_urls = [
            reverse('beranda'),
            reverse('form_pengaduan'),
            reverse('tracking'),
        ]
        for url in protected_urls:
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_login_page_generates_captcha(self):
        """Test that accessing the login page generates a captcha value in session."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('captcha_result', self.client.session)
        self.assertTrue(1 <= self.client.session['captcha_result'] <= 20)

    def test_login_fails_without_captcha(self):
        """Test that login fails when captcha_answer is missing or incorrect."""
        # Get captcha first to store it in session
        self.client.get(reverse('login'))
        
        # Post incorrect captcha answer
        response = self.client.post(reverse('login'), {
            'username_or_email': 'budi',
            'password': 'testpassword123',
            'captcha_answer': 999  # incorrect answer
        })
        self.assertEqual(response.status_code, 200)
        # Form should be invalid and not login
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('captcha_answer', response.context['form'].errors)

    def test_login_succeeds_with_correct_captcha(self):
        """Test that login succeeds with correct credentials and captcha answer."""
        self.client.get(reverse('login'))
        correct_answer = self.client.session['captcha_result']
        
        response = self.client.post(reverse('login'), {
            'username_or_email': 'budi',
            'password': 'testpassword123',
            'captcha_answer': correct_answer
        })
        # Successful login redirects to home (beranda)
        self.assertRedirects(response, reverse('beranda'))

    def test_complaint_creation_redirection_and_detail(self):
        """Test complaint submission redirects to confirmation page and details are accessible."""
        # Log in
        self.client.get(reverse('login'))
        correct_answer = self.client.session['captcha_result']
        self.client.post(reverse('login'), {
            'username_or_email': 'budi',
            'password': 'testpassword123',
            'captcha_answer': correct_answer
        })
        
        # Submit complaint form
        # We simulate posting form data without a real file (foto is blank/null is allowed)
        response = self.client.post(reverse('form_pengaduan'), {
            'kategori': 'Jalan',
            'lokasi': 'Jl. Diponegoro No 10',
            'deskripsi': 'Jalan berlubang besar dan membahayakan pengendara motor.',
        })
        
        # Verify it redirects to the confirmation view
        pengaduan = Pengaduan.objects.first()
        self.assertIsNotNone(pengaduan)
        self.assertRedirects(response, reverse('konfirmasi', kwargs={'pk': pengaduan.pk}))
        
        # Test confirmation page is viewable
        confirm_response = self.client.get(reverse('konfirmasi', kwargs={'pk': pengaduan.pk}))
        self.assertEqual(confirm_response.status_code, 200)
        self.assertContains(confirm_response, f"#SPID-{pengaduan.pk}")
        
        # Test detail page is viewable
        detail_response = self.client.get(reverse('user_detail', kwargs={'pk': pengaduan.pk}))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Timeline Penanganan")

    def test_root_url_redirects_to_login(self):
        """Test that visiting the root URL redirects to the login page."""
        response = self.client.get('/')
        self.assertRedirects(response, reverse('login'))

    def test_profile_requires_login(self):
        """Test that accessing the profile page requires login."""
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

    def test_profile_view_get(self):
        """Test profile page renders correctly with user data when logged in."""
        self.client.login(username='budi', password='testpassword123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kelola Profil')
        self.assertContains(response, 'budi')
        self.assertContains(response, 'Budi Cahyono')

    def test_profile_update_post(self):
        """Test updating profile details successfully, including uploading an image."""
        self.client.login(username='budi', password='testpassword123')
        
        # Create a valid mock image using Pillow
        file_mock = io.BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file_mock, 'png')
        file_mock.seek(0)
        
        mock_image = SimpleUploadedFile(
            name='test_avatar.png',
            content=file_mock.read(),
            content_type='image/png'
        )

        response = self.client.post(reverse('profile'), {
            'nama_lengkap': 'Budi Prasetyo',
            'email': 'budiprasetyo@gmail.com',
            'nomor_hp': '089999999999',
            'foto_profil': mock_image
        })
        self.assertRedirects(response, reverse('profile'))
        
        # Verify database was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.nama_lengkap, 'Budi Prasetyo')
        self.assertEqual(self.user.email, 'budiprasetyo@gmail.com')
        self.assertEqual(self.user.nomor_hp, '089999999999')
        self.assertTrue(self.user.foto_profil.name.endswith('.png'))

    def test_admin_export_page(self):
        """Test admin export page loads correctly for staff members."""
        self.client.login(username='admin_test', password='adminpassword123')
        response = self.client.get(reverse('admin_export'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Export Laporan Berkala')

    def test_admin_users_management(self):
        """Test admin list and adding admin user."""
        self.client.login(username='admin_test', password='adminpassword123')
        response = self.client.get(reverse('admin_users'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manajemen Admin & Pengguna')

        # Add a new admin
        response = self.client.post(reverse('admin_users'), {
            'username': 'new_admin',
            'nama_lengkap': 'New Administrator',
            'email': 'new@spid.gov',
            'nomor_hp': '087777777777',
            'password': 'newpassword123'
        })
        self.assertRedirects(response, reverse('admin_users'))
        
        # Verify user is created in database
        self.assertTrue(CustomUser.objects.filter(username='new_admin', is_staff=True).exists())

    def test_admin_profile_update(self):
        """Test admin profile update page GET and POST."""
        self.client.login(username='admin_test', password='adminpassword123')
        response = self.client.get(reverse('admin_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kelola Profil Admin')

        # Update profile details
        response = self.client.post(reverse('admin_profile'), {
            'nama_lengkap': 'Admin SPID Baru',
            'email': 'admin_updated@spid.gov',
            'nomor_hp': '089999999991'
        })
        self.assertRedirects(response, reverse('admin_profile'))
        
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.nama_lengkap, 'Admin SPID Baru')
        self.assertEqual(self.admin.email, 'admin_updated@spid.gov')
        self.assertEqual(self.admin.nomor_hp, '089999999991')

    def test_admin_delete_complaint_success(self):
        """Test that admin can successfully delete a complaint via POST."""
        complaint = Pengaduan.objects.create(
            user=self.user,
            kategori='Jalan',
            lokasi='Jl. Kebon Jeruk No 5',
            deskripsi='Ada lubang di tengah jalan.',
            status='Pending'
        )
        self.assertEqual(Pengaduan.objects.count(), 1)
        
        self.client.login(username='admin_test', password='adminpassword123')
        response = self.client.post(reverse('admin_delete', kwargs={'pk': complaint.pk}))
        self.assertRedirects(response, reverse('admin_data'))
        self.assertEqual(Pengaduan.objects.count(), 0)

    def test_non_admin_cannot_delete_complaint(self):
        """Test that regular users cannot delete a complaint."""
        complaint = Pengaduan.objects.create(
            user=self.user,
            kategori='Jalan',
            lokasi='Jl. Kebon Jeruk No 5',
            deskripsi='Ada lubang di tengah jalan.',
            status='Pending'
        )
        self.assertEqual(Pengaduan.objects.count(), 1)
        
        self.client.login(username='budi', password='testpassword123')
        response = self.client.post(reverse('admin_delete', kwargs={'pk': complaint.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin_login'), response.url)
        self.assertEqual(Pengaduan.objects.count(), 1)
