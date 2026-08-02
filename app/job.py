


class Jobs:
    
    def __init__(self):
        self.jobs = []

    def add_job(self,job):
        self.jobs.append(job)
        
    def get_jobs(self):
        return self.jobs
    def delete_job(self,job_number):
        all_jobs = self.jobs
        self.jobs = [job for job in all_jobs if job.job_number != job_number]
                


class SingleJob(Jobs):
    
    def __init__(self,command,job_number,pid,status,process):
        self.process = process
        self.job_number = job_number
        self.command = command
        self.pid = pid
        self.status = status
        
jobs = Jobs()