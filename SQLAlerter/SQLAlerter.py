#Alerts a user once a specific Script or MSSQL job has completed on a SQL Server.
PUSHOVER_CLIENT_ID = ""
PUSHOVER_API_KEY = ""
MSSQL_DOMAIN = False #Use Domain Authentication?
MSSQL_USER = "" 
MSSQL_PASS = ""

from sqlalchemy.sql import text
from pushover import init, Client
init(PUSHOVER_API_KEY)

class Job(object):
    name = None
    session_id = None
    job_id = None
    start_execution_date = None
    def __init__(self,name,session_id,job_id,start_execution_date):
        self.name = name
        self.sesion_id = session_id
        self.job_id = job_id
        self.start_execution_date = start_execution_date

    def __str__(self):
        return "%s started at %s" % (self.name, self.start_execution_date)

    def is_running(self,server):
        """ Check's to see if this job is still running."
        """
        result = server.execute(text("""SELECT COUNT(*)
                                FROM msdb.dbo.sysjobactivity AS sja
                                INNER JOIN msdb.dbo.sysjobs AS sj ON sja.job_id = sj.job_id
                                WHERE sja.start_execution_date IS NOT NULL
                                   AND sja.stop_execution_date IS NULL
                                   AND run_requested_date >= CONVERT(date,GETDATE()) AND name='%s' and sja.job_id = '%s' and start_execution_date =  :starttime""" % (self.name, self.job_id)), starttime= self.start_execution_date)
        output = result.fetchall()
        return bool(output[0][0] > 0)


class Script(object):
    text = None
    session_id = None
    command = None
    start_time = None
    def __init__(self,text,session_id,command,start_time):
        self.text = text
        self.session_id = session_id
        self.command = command
        self.start_time = start_time

    def __str__(self):
        return "%s at %s with text = %s" % (self.command, self.start_time, self.text[:50])

    def is_running(self,server):
        """ Check's to see if this script is still running.
        """
        result = server.execute(text("""SELECT COUNT(*)
                        FROM sys.dm_exec_requests req
                        CROSS APPLY sys.dm_exec_sql_text(sql_handle) AS sqltext
                        WHERE start_time = :starttime and command = '%s' and session_id = %s """ % ( self.command, self.session_id)),starttime= self.start_time)
        output = result.fetchall()
        return bool(output[0][0] > 0)

def load_jobs(server):
    """ Load the jobs into a list
    """
    returned_values = []
    results = server.execute("""SELECT name, session_id, sja.job_id, start_execution_date
            FROM msdb.dbo.sysjobactivity AS sja
            INNER JOIN msdb.dbo.sysjobs AS sj ON sja.job_id = sj.job_id
            WHERE sja.start_execution_date IS NOT NULL
               AND sja.stop_execution_date IS NULL
               AND run_requested_date >= CONVERT(date,GETDATE())""")
    for row in results:
        job_result = Job(row[0],row[1],row[2],row[3])
        returned_values.append(job_result)
    return returned_values

def load_scripts(server):
    """ Load the scripts into a list
    """
    returned_values = []
    results = server.execute("""SELECT text, session_id, command, start_time
                            FROM sys.dm_exec_requests req
                            CROSS APPLY sys.dm_exec_sql_text(sql_handle) AS sqltext""")
    for row in results:
        script_result = Script(row[0],row[1],row[2],row[3])
        returned_values.append(script_result)
    return returned_values

if __name__ == "__main__":
    import sqlalchemy
    server_conn = raw_input("Type in Server Address:  ")
    server = None
    if MSSQL_DOMAIN:
        server = sqlalchemy.create_engine("mssql+pyodbc://@%s/master" % (server_conn))
    else:
        server = sqlalchemy.create_engine("mssql+pyodbc://%s:%s@%s/master" % (MSSQL_USER,MSSQL_PASS,server_conn))
    assert(server is not None)
    print "Are you waiting for a"
    print "1. SQL Job"
    print "2. Stored Procedure / Script"
    type_input = raw_input("Enter the type number:  ")
    assert(int(type_input)) #Input must be a valid integer.
    type_input = int(type_input)
    task_to_check = None
    if type_input == 1:
        print "Task Selected: SQL Job"
        jobs = load_jobs(server)
        for x, job in enumerate(jobs):
            print "%s. %s" % (x,job)
        task_to_check = jobs[int(raw_input("Type in SQL Job number to follow:  "))]
    if type_input == 2:
        print "Task Selected: Stored Procedure / Script"
        stored_procedures = load_scripts(server)
        for sp, x in enumerate(stored_procedures):
            print "%s. %s" % (sp, x)
        task_to_check = stored_procedures[int(raw_input("Type in SQL Script number to follow:  "))]
    from time import sleep
    while True:
        result = task_to_check.is_running(server)
        if result == 0:
            print "Task has completed."
            #Send an Alert via Pushover.
            client = Client(PUSHOVER_CLIENT_ID).send_message("The task you were waiting on in MSSQL has completed!")
            break
        print "Going to sleep - still sleeping"
        sleep(15)
        