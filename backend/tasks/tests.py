from django.test import TestCase

from .models import Task


class FrontendSmokeTests(TestCase):
    def test_index_page_renders(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Task")
        self.assertContains(response, "Description")
        self.assertContains(response, "/api/")


class TaskApiTests(TestCase):
    def test_create_list_update_and_delete_task(self):
        create_response = self.client.post(
            "/api/",
            data={
                "title": "Write smoke tests",
                "description": "Verify frontend and API stay in sync",
                "priority": "high",
            },
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 201)
        task_id = create_response.json()["id"]

        list_response = self.client.get("/api/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(list_response.json()[0]["title"], "Write smoke tests")
        self.assertEqual(
            list_response.json()[0]["description"],
            "Verify frontend and API stay in sync",
        )

        patch_response = self.client.patch(
            f"/api/{task_id}/",
            data={"status": "completed"},
            content_type="application/json",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["status"], "completed")

        delete_response = self.client.delete(f"/api/{task_id}/")
        self.assertEqual(delete_response.status_code, 204)
        self.assertTrue(Task.objects.filter(id=task_id, is_deleted=True).exists())
        self.assertEqual(self.client.get("/api/").json(), [])
