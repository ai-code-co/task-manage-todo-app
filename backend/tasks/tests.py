from django.test import TestCase
from django.urls import reverse

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
        list_url = reverse("task-list")
        create_response = self.client.post(
            list_url,
            data={
                "title": "Write smoke tests",
                "description": "Verify frontend and API stay in sync",
                "priority": "high",
            },
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 201)
        task_id = create_response.json()["id"]

        list_response = self.client.get(list_url)
        self.assertEqual(list_response.status_code, 200)
        payload = list_response.json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["title"], "Write smoke tests")
        self.assertEqual(
            payload["results"][0]["description"],
            "Verify frontend and API stay in sync",
        )

        patch_response = self.client.patch(
            reverse("task-detail", args=[task_id]),
            data={"status": "completed"},
            content_type="application/json",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["status"], Task.STATUS_COMPLETED)

        delete_response = self.client.delete(reverse("task-detail", args=[task_id]))
        self.assertEqual(delete_response.status_code, 204)
        self.assertTrue(Task.objects.filter(id=task_id, is_deleted=True).exists())
        empty_payload = self.client.get(list_url).json()
        self.assertEqual(empty_payload["count"], 0)
        self.assertEqual(empty_payload["results"], [])

    def test_page_size_query_param_is_honored(self):
        for index in range(25):
            Task.objects.create(title=f"Task {index}")

        response = self.client.get(reverse("task-list"), {"page_size": 5})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 25)
        self.assertEqual(len(payload["results"]), 5)

    def test_complete_action_marks_task_completed(self):
        task = Task.objects.create(title="Use complete action")

        response = self.client.post(reverse("task-complete", args=[task.id]))

        self.assertEqual(response.status_code, 204)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.STATUS_COMPLETED)
