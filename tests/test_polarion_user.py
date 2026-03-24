import unittest

from keys import polarion_password, polarion_project_id, polarion_url, polarion_user

from polarion.polarion import Polarion
from polarion.user import User


class TestPolarionUser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pol = Polarion(polarion_url, polarion_user, polarion_password)
        cls.executing_project = cls.pol.getProject(polarion_project_id)

    def setUp(self):
        pass

    def test_non_existent_user(self):
        all_users = self.executing_project.getUsers()
        broken_uri = all_users[0].uri + "broken"

        with self.assertRaises(Exception):
            User(self.pol, None, broken_uri)
