from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger


class ScriptScheduler:
    def __init__(self):
        self._scheduler = BackgroundScheduler()
        self._scheduler.start()
        self._jobs = {}

    def schedule(self, job_id: str, run_at: datetime, callback, *args):
        """
        Schedule a one-shot job. The callback is what actually runs the script —
        typically something like player.start(script).
        """
        if job_id in self._jobs:
            self.cancel(job_id)

        trigger = DateTrigger(run_date=run_at)
        job = self._scheduler.add_job(callback, trigger, args=args, id=job_id)
        self._jobs[job_id] = job
        return job

    def cancel(self, job_id: str) -> bool:
        if job_id in self._jobs:
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass
            del self._jobs[job_id]
            return True
        return False

    def cancel_all(self):
        for jid in list(self._jobs):
            self.cancel(jid)

    def list_jobs(self):
        return {
            jid: {
                "next_run": str(job.next_run_time) if job.next_run_time else "done",
            }
            for jid, job in self._jobs.items()
        }

    def shutdown(self):
        self.cancel_all()
        self._scheduler.shutdown(wait=False)
