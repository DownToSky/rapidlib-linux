""" the parent class of app-specific methods
Developers will inherit from this class to implement the app-specific
methods. RAPID(C) will run their
implementations to
1) get the groundtruth of the app by running the app in default mode.
2) get the training data by running the app in different configurations
"""


class AppMethods():
    PCM_PREFIX = [
        '/home/liuliu/Research/pcm/pcm.x', '0.5', '-nc', '-ns', '2>/dev/null',
        '-csv=tmp.csv', '--'
    ]

    def __init__(self, name, obj_path):
        """ Initialization with app name
        :param name:
        """
        self.appName = name
        self.obj_path = obj_path
        self.sys_usage_table = SysUsageTable()
        self.training_units = 1
        self.fullrun_units = 1

    def setTrainingUnits(self, unit):
        self.training_units = unit

    def getCommandWithConfig(self, config_str, qosRun=False, fullRun=True):
        ''' use config string to generate a config and get command '''
        elements = config_str.split('-')
        configs = []
        for i in range(0, len(elements)):
            if i % 2 == 0:  # knob name
                knob = Knob(elements[i], elements[i], -99999, 99999)
                configs.append(Config(knob, elements[i + 1]))
                i += 1
        return self.getCommand(configs, qosRun, fullRun)

    # Implement this function
    def getCommand(self, configs=None, qosRun=False, fullRun=True):
        """ Assembly the CMD line for running the app
        :param configs: a concrete configuration with knob settings
                        Default setting would assemble command for GT
        """
        return ""

    def getFullRunCommand(self, budget):
        pass

    def parseLog(self):
        name = "./mission_" + self.appName + "_log.csv"
        # go to the last line
        with open(name) as logfile:
            for line in logfile:
                pass
            last_col = line.split(',')
            totTime = float(last_col[-5])
            totReconfig = int(last_col[-4])
            success = last_col[-1].rstrip()
        # find details
        df = pd.read_csv(name)
        triggered_by_budget = df['RC_by_budget'].sum()
        return {
            'totTime': totTime,
            'totReconfig': totReconfig,
            'success': success,
            'rc_by_budget': triggered_by_budget
        }

    def overheadMeasure(self, budget=0.5):
        print("measuring overhead")
        #self.runGT(True)
        budget = (self.min_cost + budget * (self.max_cost - self.min_cost)
                  ) * self.fullrun_units / 1000.0  #budget in the middle
        report = []
        # generate the possible units
        units = list(range(1, 20)) + list(range(20, 101, 10))
        for unit in units:
            if int(self.fullrun_units / unit) < 1:
                # finest granularity
                continue
            cmd = self.getFullRunCommand(budget, UNIT=unit)
            for i in range(1, 3):  # for each run, 5 times
                print("running budget", str(budget), "itr", str(i))
                start_time = time.time()
                os.system(" ".join(cmd))
                elapsed_time = time.time() - start_time
                mv = self.getQoS()
                if type(mv) is list:
                    mv = mv[-1]  # use the default qos metric
                logger = self.parseLog()
                totTime = logger['totTime']
                totReconfig = logger['totReconfig']
                success = logger['success']
                triggered_by_budget = logger['rc_by_budget']
                report.append({
                    'Unit':
                    unit,
                    'MV':
                    mv,
                    'Augmented_MV':
                    0.0 if elapsed_time > 1.05 * budget else mv,
                    'Budget':
                    budget,
                    'Exec_Time':
                    elapsed_time,
                    'OverBudget':
                    elapsed_time > 1.05 * budget,
                    'RC_TIME':
                    totTime,
                    'RC_NUM':
                    totReconfig,
                    'SUCCESS':
                    success,
                    'overhead_pctg':
                    float(totTime) / (1000.0 * float(elapsed_time)),
                    'RC_by_budget':
                    triggered_by_budget
                })
        return report

    def qosRun(self, OFFLINE=False):
        print("running QOS run")
        self.runGT(True)  # first generate the groundtruth
        step_size = (self.max_cost - self.min_cost) / 10.0
        report = []
        for percentage in range(1, 11):
            budget = (self.min_cost + float(percentage) *
                      step_size) * self.fullrun_units / 1000.0
            unit = self.fullrun_units / 10  # reconfig 10 times
            print("RUNNING BUDGET:", str(budget))
            cmd = self.getFullRunCommand(budget, OFFLINE=OFFLINE)
            start_time = time.time()
            os.system(" ".join(cmd))
            elapsed_time = time.time() - start_time
            mv = self.getQoS()
            if type(mv) is list:
                mv = mv[-1]  # use the default qos metric
            report.append({
                'Percentage':
                percentage,
                'MV':
                mv,
                'Augmented_MV':
                0.0 if elapsed_time > 1.05 * budget else mv,
                'Budget':
                budget,
                'Exec_Time':
                elapsed_time
            })
            print("mv:" + str(mv))
        return report

    # Implement this function
    def train(self,
              config_table,
              bb_profile,
              numOfFixedEnv,
              appInfo,
              upload=False):
        """ Train the application with all configurations in config_table and
        write Cost / Qos in costFact and mvFact.
        :param config_table: A table of class Profile containing all
        configurations to train
        :param bb_profile: A table of class Profile containing all
        configurations(invalid+valid)
        :param numOfFixedEnv: number of environments if running for fixed env
        :param appInfo: a obj of Class AppSummary
        :param upload: whether to upload the measuremnet to RAPID_M server
        """
        # perform a single run for training
        configurations = config_table.configurations  # get the
        configurations_bb = bb_profile.configurations
        # configurations in the table
        train_conf = appInfo.TRAINING_CFG
        withMV = train_conf['withQoS']
        withSys = train_conf['withSys']
        withPerf = train_conf['withPerf']
        withMModel = train_conf['withMModel']
        costFact = open(appInfo.FILE_PATHS['COST_FILE_PATH'], 'w')
        if withMV:
            mvFact = open(appInfo.FILE_PATHS['MV_FILE_PATH'], 'w')
        if withSys:
            sysFact = open(appInfo.FILE_PATHS['SYS_FILE_PATH'], 'w')
        if withPerf:
            slowdownProfile = open(appInfo.FILE_PATHS['PERF_FILE_PATH'], 'w')
            slowdownHeader = False
        if withMModel:
            m_slowdownProfile = open(appInfo.FILE_PATHS['M_FILE_PATH'], 'w')
            m_slowdownHeader = False

        # comment the lines below if need random coverage
        multi_env = SysArgs()
        single_env = Stresser(self.appName)
        env_commands = []
        if numOfFixedEnv != -1:
            # half single half multi
            for i in range(0, int(numOfFixedEnv /
                                  2)):  # run different environment
                #env_commands.append(env.getRandomEnv())
                env_commands.append(single_env.getRandomStresser())
                env_commands.append(multi_env.getRandomEnv())
        training_time_record = {}

        # iterate through configurations
        total = len(configurations_bb)
        current = 1
        for configuration in configurations_bb:
            print("*****RUNNING:" + str(current) + "/" + str(total) + "*****")
            current += 1
            # the purpose of each iteration is to fill in the two values below
            cost = 0.0
            mv = [0.0]
            configs = configuration.retrieve_configs(
            )  # extract the configurations
            # assembly the command
            command = self.getCommand(configs, fullRun=False)

            if not appInfo.isTrained():
                # 1) COST Measuremnt
                total_time, cost, metric = self.getCostAndSys(
                    command, self.training_units, withSys,
                    configuration.printSelf('-'))
                training_time_record[configuration.printSelf('-')] = total_time
                # write the cost to file
                AppMethods.writeConfigMeasurementToFile(
                    costFact, configuration, cost)
                # 2) MV Measurement
                if withMV:
                    mv = self.getQoS()
                    # write the mv to file
                    AppMethods.writeConfigMeasurementToFile(
                        mvFact, configuration, mv)
            if not appInfo.isPerfTrained():
                # 3) SYS Profile Measurement
                if withSys:
                    self.recordSysUsage(configuration, metric)
                # 4) Performance Measurement
                if withPerf:
                    # examine the execution time slow-down
                    print("START STRESS TRAINING")
                    slowdownTable, m_slowdownTable = self.runStressTest(
                        configuration, cost, env_commands, withMModel)
                    # write the header
                    if not slowdownHeader:
                        slowdownProfile.write(metric.printAsHeader(','))
                        slowdownProfile.write(",SLOWDOWN")
                        slowdownProfile.write('\n')
                        if withMModel:
                            m_slowdownProfile.write(metric.printAsHeader(','))
                            m_slowdownProfile.write(",SLOWDOWN")
                            m_slowdownProfile.write('\n')
                        slowdownHeader = True
                    slowdownTable.writeSlowDownTable(slowdownProfile)
                    if withMModel:
                        m_slowdownTable.writeSlowDownTable(m_slowdownProfile)
                # 5) train the slowdown given a known environment
                #if withMModel:
                #print("START MModel Testing")
                #m_slowdownTable = self.runMModelTest(configuration, cost)
                #m_slowdownTable.writeSlowDownTable(m_slowdownProfile)
            self.cleanUpAfterEachRun(configs)
        # write the metric to file
        costFact.close()
        if withMV:
            mvFact.close()
        if withSys:
            self.printUsageTable(sysFact)
        if withPerf:
            slowdownProfile.close()
        if withMModel:
            m_slowdownProfile.close()
        if upload:
            print("preparing to upload to server")
            self.uploadToServer(appInfo)
        # udpate the status
        appInfo.setTrained()
        appInfo.setPerfTrained()
        return training_time_record

    # Send the system profile up to the RAPID_M server
    def uploadToServer(self, appInfo):
        # get the app system profile text
        with open(appInfo.FILE_PATHS['SYS_FILE_PATH'], 'r') as sysF:
            sys_data = sysF.read()
        # get the app performance profile text
        with open(appInfo.FILE_PATHS['PERF_FILE_PATH'], 'r') as perfF:
            perf_data = perfF.read()
        with open(appInfo.FILE_PATHS['MV_FILE_PATH'], 'r') as perfF:
            mv_data = perfF.read()
        with open(appInfo.FILE_PATHS['COST_FILE_PATH'], 'r') as perfF:
            cost_data = perfF.read()
        # get the machine id
        hostname = socket.gethostname()

        INIT_ENDPOINT = "http://algaesim.cs.rutgers.edu/rapid_server/init.php"
        INIT_ENDPOINT = INIT_ENDPOINT + "?" + 'machine=' + hostname + \
            '&app=' + appInfo.APP_NAME

        # set up the post params
        POST_PARAMS = {
            'buckets': sys_data,
            'p_model': perf_data,
            'mv': mv_data,
            'cost': cost_data
        }

        req = requests.post(url=INIT_ENDPOINT, data=POST_PARAMS)

        response = req.text
        print("response:" + response)

    # Implement this function
    def runGT(self, qosRun=False):
        """ Perform a default run of non-approxiamte version of the
        application to generate groundtruth result for
        QoS checking later in the future. The output can be application
        specific, but we recommend to output the
        result to a file.
        """
        print("GENERATING GROUND TRUTH for " + self.appName)
        command = self.getCommand(None, qosRun, fullRun=False)
        os.system(" ".join(command))
        self.afterGTRun()

    def runStressTest(self,
                      configuration,
                      orig_cost,
                      env_commands=[],
                      withMModel=False):
        app_command = self.getCommand(configuration.retrieve_configs(),
                                      fullRun=False,
                                      qosRun=False)
        env = SysArgs()
        slowdownTable = SlowDown(configuration)
        m_slowdownTable = SlowDown(configuration)
        # if running random coverage, create the commands
        if len(env_commands) == 0:
            print("No commands input, get 10 synthetic stressers")
            for i in range(0, 10):  # run 10 different environment
                env_command = env.getRandomEnv()
                env_commands.append(env_command)
        id = 0
        for env_command in env_commands:
            # if withMModel, check the environment first
            if withMModel:
                print('running stresser alone', env_command['configuration'],
                      id, env_command['command'])
                id += 1
                #command = " ".join(self.PCM_PREFIX + env_command + ['-t', '5'])
                #os.system(command)
                command = " ".join(self.PCM_PREFIX + env_command['command'] +
                                   ['2> /dev/null'])
                info = env_command['app'] + ":" + env_command['configuration']
                env_metric = None
                while env_metric is None:
                    # broken, rerun
                    os.system('rm tmp.csv')
                    stresser = subprocess.Popen(command,
                                                shell=True,
                                                preexec_fn=os.setsid)
                    time.sleep(5)  #profile for 5 seconds
                    os.killpg(os.getpgid(stresser.pid), signal.SIGKILL)
                    env_metric = AppMethods.parseTmpCSV()

            # start the env
            #env_creater = subprocess.Popen(
            #    " ".join(env_command), shell=True, preexec_fn=os.setsid)
            print('running stresser+app')
            env_creater = subprocess.Popen(" ".join(env_command['command'] +
                                                    ['&> /dev/null']),
                                           shell=True,
                                           preexec_fn=os.setsid)

            total_time, cost, metric = self.getCostAndSys(
                app_command, self.training_units, True,
                configuration.printSelf('-'))
            # end the env
            os.killpg(os.getpgid(env_creater.pid), signal.SIGKILL)
            # write the measurement to file
            slowdown = cost / orig_cost
            slowdownTable.add_slowdown(metric, slowdown)
            if withMModel:
                m_slowdownTable.add_slowdown(env_metric, slowdown, info)
        return slowdownTable, m_slowdownTable

    def runMModelTest(self, configuration, orig_cost):
        app_command = self.getCommand(configuration.retrieve_configs())
        env = SysArgs()
        slowdownTable = SlowDown(configuration)
        # if running random coverage, create the commands
        for i in range(0, 5):  # run 5 different environment
            env_command = env.getRandomEnv()
            # measure the env
            command = " ".join(self.PCM_PREFIX + env_command + ['-t', '5'])
            os.system(command)
            env_metric = AppMethods.parseTmpCSV()
            # measure the combined env
            env_creater = subprocess.Popen(" ".join(env_command),
                                           shell=True,
                                           preexec_fn=os.setsid)
            total_time, cost, total_metric = self.getCostAndSys(
                app_command, self.training_units, True,
                configuration.printSelf('-'))
            # end the env
            os.killpg(os.getpgid(env_creater.pid), signal.SIGKILL)
            # write the measurement to file
            slowdown = cost / orig_cost
            slowdownTable.add_slowdown(env_metric, slowdown)
        return slowdownTable

    # Some default APIs
    def getName(self):
        """ Return the name of the app
        :return: string
        """
        return self.name

    # some utilities might be useful
    def getCostAndSys(self,
                      command,
                      work_units=1,
                      withSys=False,
                      configuration=''):
        """ return the execution time of running a single work unit using
        func in milliseconds
        To measure the cost of running the application with a configuration,
        each training run may finish multiple
        work units to average out the noise.
        :param command: The shell command to use in format of ["app_binary",
        "arg1","arg2",...]
        :param work_units: The total work units in each run
        :param withSys: whether to check system usage or not
        :return: the average execution time for each work unit
        """
        # remove csv if exists
        if os.path.isfile('./tmp.csv'):
            os.system('rm tmp.csv')
        time1 = time.time()
        metric_value = None
        if withSys:
            # reassemble the command with pcm calls
            # sudo ./pcm.x -csv=results.csv
            command = self.PCM_PREFIX + command
        os.system(" ".join(command))
        time2 = time.time()
        total_time = time2 - time1
        avg_time = (time2 - time1) * 1000.0 / work_units
        # parse the csv
        if withSys:
            #if total_time<1000:
            # the time is too small for parsetmpcsv

            metric_value = AppMethods.parseTmpCSV()
            while metric_value is None:
                print("rerun", " ".join(command))
                # rerun
                os.system('rm tmp.csv')
                os.system(" ".join(command))
                metric_value = AppMethods.parseTmpCSV()
        return total_time, avg_time, metric_value

    @staticmethod
    def parseTmpCSV():
        metric_value = Metric()
        with open('tmp.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            line_count = 0
            metric = []
            values = []
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                elif line_count == 1:  # header line
                    if len(row) != 34:  #broken line
                        print("tmp csv file broken with line", len(row))
                        return None
                    for item in row:
                        metric.append(item)
                    line_count += 1
                else:  # value line
                    value = []
                    if len(row) != len(metric):
                        # discard the row, especially the last row
                        continue
                    for item in row:
                        value.append(item)
                    values.append(value)
            for i in range(0, len(metric)):
                if metric[i] != '':
                    try:
                        float(values[0][i])
                    except:
                        if i <= 1:
                            continue
                        else:
                            print("not valid number found in csv", values[0],
                                  i)
                            return None
                    # calculate the average value
                    avg_value = functools.reduce(
                        (lambda x, y: (float(y[i]) + float(x))), values,
                        0.) / float(len(values))
                    if avg_value == -1:
                        # broken line
                        print('-1 found in line')
                        return None
                    metric_value.add_metric(metric[i], avg_value)
        csv_file.close()
        return metric_value

    def getScaledQoS(self):
        ''' return the scaled QoS from 0 to 100 '''
        return self.getQoS()

    def getQoS(self):
        """ Return the QoS for a configuration"""
        return [0.0]

    def moveFile(self, fromfile, tofile):
        """ move a file to another location
        :param fromfile: file current path
        :param tofile: file new path
        """
        command = ["mv", fromfile, tofile]
        os.system(" ".join(command))

    @staticmethod
    def writeConfigMeasurementToFile(filestream, configuration, values):
        """ write a configuration with its value (could be cost or mv) to a
        opened file stream
        :param filestream: the file stream, need to be opened with 'w'
        :param configuration: the configuration
        :param value: the value in double or string
        """
        filestream.write(configuration.printSelf() + " ")
        if type(values) is list:
            for value in values:
                filestream.write(str(value) + " ")
        else:
            filestream.write(str(values))
        filestream.write('\n')

    def recordSysUsage(self, configuration, metric):
        """ record the system usage of a configuration
        :param configuration: the configuration
        :param metric: the dict of metric measured
        """
        self.sys_usage_table.add_entry(configuration.printSelf('-'), metric)

    def printUsageTable(self, filestream):
        self.sys_usage_table.printAsCSV(filestream, ',')

    def cleanUpAfterEachRun(self, configs=None):
        """ This function will be called after every training iteration for a
        config
        """
        pass

    def afterGTRun(self):
        """ This function will be called after runGT()
        """
        pass

    def computeQoSWeight(self, preferences, values):
        """ This function will be called by C++ end to finalize a xml
        """
        return 0.0

    def pinTime(self, filestream):
        filestream.write(str(datetime.datetime.now()) + " ")