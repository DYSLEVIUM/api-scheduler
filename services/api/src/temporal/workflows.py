from datetime import timedelta
from uuid import UUID

from temporalio import workflow


@workflow.defn
class IntervalScheduleWorkflow:
    @workflow.run
    async def run(self, schedule_id: UUID) -> None:
        run_number = 1

        while True:
            schedule_data = await workflow.execute_activity(
                "get_schedule_and_target",
                args=(schedule_id,),
                start_to_close_timeout=timedelta(seconds=10),
            )

            if schedule_data.get("deleted"):
                return

            if schedule_data.get("paused"):
                await workflow.sleep(timedelta(seconds=30))
                continue

            schedule = schedule_data["schedule"]
            target = schedule_data["target"]
            url = schedule_data["url"]

            request_result = await workflow.execute_activity(
                "execute_http_request",
                args=(url, target["method"],
                      target["headers"], target["body"]),
                start_to_close_timeout=timedelta(seconds=60),
            )

            await workflow.execute_activity(
                "create_job_record",
                args=(schedule_id, run_number, request_result),
                start_to_close_timeout=timedelta(seconds=10),
            )

            run_number += 1
            await workflow.sleep(timedelta(seconds=schedule["interval_seconds"]))


@workflow.defn
class WindowScheduleWorkflow:
    @workflow.run
    async def run(self, schedule_id: UUID) -> None:
        schedule_data = await workflow.execute_activity(
            "get_schedule_and_target",
            schedule_id,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if schedule_data.get("deleted"):
            return

        if schedule_data.get("paused"):
            return

        schedule = schedule_data["schedule"]
        target = schedule_data["target"]
        url = schedule_data["url"]

        if "duration_seconds" not in schedule:
            return

        duration = timedelta(seconds=schedule["duration_seconds"])
        interval = timedelta(seconds=schedule["interval_seconds"])
        end_time = workflow.now() + duration
        run_number = 1

        while workflow.now() < end_time:
            current_schedule_data = await workflow.execute_activity(
                "get_schedule_and_target",
                schedule_id,
                start_to_close_timeout=timedelta(seconds=10),
            )

            if current_schedule_data.get("deleted"):
                return

            if current_schedule_data.get("paused"):
                break

            current_target = current_schedule_data["target"]
            current_url = current_schedule_data["url"]

            request_result = await workflow.execute_activity(
                "execute_http_request",
                args=(current_url, current_target["method"],
                      current_target["headers"], current_target["body"]),
                start_to_close_timeout=timedelta(seconds=60),
            )

            await workflow.execute_activity(
                "create_job_record",
                args=(schedule_id, run_number, request_result),
                start_to_close_timeout=timedelta(seconds=10),
            )

            run_number += 1

            next_run_time = workflow.now() + interval
            if next_run_time < end_time:
                await workflow.sleep(interval)
            else:
                break
