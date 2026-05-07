import unittest
import time

from gui_do import TaskScheduler


class TaskSchedulerDispatchBatchingTests(unittest.TestCase):
    def test_dispatch_limit_is_honored_with_batched_dispatch(self):
        scheduler = TaskScheduler(max_workers=1)
        self.addCleanup(scheduler.shutdown)

        scheduler.set_message_dispatch_limit(3)
        scheduler.set_message_ingest_limit(None)
        received = []

        def produce(task_id):
            for i in range(10):
                scheduler.send_message(task_id, i)
            return None

        scheduler.add_task("producer", produce, message_method=received.append)

        deltas = []
        deadline = time.perf_counter() + 2.0
        while time.perf_counter() < deadline:
            before = len(received)
            scheduler.update()
            after = len(received)
            if after > before:
                deltas.append(after - before)
            if not scheduler.tasks_busy():
                break
            time.sleep(0.001)

        self.assertEqual(list(range(10)), received)
        self.assertTrue(deltas)
        self.assertTrue(all(delta <= 3 for delta in deltas))


if __name__ == "__main__":
    unittest.main()
