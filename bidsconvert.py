import argparse
import json
import os
import subprocess
from bids import BIDSLayout
import datetime
from collections import OrderedDict
from shutil import copy as fileCopy
from shutil import rmtree

def isTrue(arg):
    return arg is not None and (arg == 'Y' or arg == '1' or arg == 'True')

def logtext(logfile, textstr):
    stamp=datetime.datetime.now().strftime("%m-%d-%y %H:%M:%S%p")
    textstring =  str(stamp) + '  ' + str(textstr)
    print(textstring)
    logfile.write(textstring + '\n')

def createDatasetDescription(bidsDir,project):
    datasetjson=os.path.join(bidsDir,'dataset_description.json');
    if not os.path.exists(datasetjson):
        print("Constructing BIDS dataset description")
        dataset_description=OrderedDict()
        dataset_description['Name'] =project
        dataset_description['BIDSVersion']=BIDSVERSION
        dataset_description['License']=""
        dataset_description['ReferencesAndLinks']=""
        with open(datasetjson,'w') as datasetjson:
             json.dump(dataset_description,datasetjson)



BIDSVERSION = "1.0.0"

parser = argparse.ArgumentParser(description="Run dcm2niix on every file in a session")
parser.add_argument("--subject", help="Subject Label", required=True)
parser.add_argument("--session_label", help="session Label",  nargs='?', required=False)
parser.add_argument("--proc_steps", help="additional proc steps",  nargs='?', required=False)
parser.add_argument("--dicomdir", help="Root output directory for DICOM files", required=True)
parser.add_argument("--niftidir", help="Root output directory for NIFTI files", required=True)
parser.add_argument("--workdir", help="working directory for temporary files", required=False,default="/tmp")
parser.add_argument("--bidsconfig", help="path to BIDS config file", required=True)
parser.add_argument("--bidsaction", help="path to BIDS action file", required=False)
parser.add_argument("--overwrite", help="Overwrite NIFTI files if they exist")
parser.add_argument("--cleanup", help="Attempt to clean up temporary files")
parser.add_argument('--version', action='version', version='%(prog)s 0.1')

args, unknown_args = parser.parse_known_args()
subject = args.subject
session_label = args.session_label
if session_label is None:
    session_label='nosession'
if not session_label:
    session_label='nosession'
overwrite = isTrue(args.overwrite)
cleanup = isTrue(args.cleanup)
dicomdir = args.dicomdir
niftidir = args.niftidir
workdir = args.workdir
logdir = niftidir + "/logs"

bidsactionfile = args.bidsaction
if bidsactionfile is None:
    bidsactionfile=''
dcm2bids_config = args.bidsconfig

proc_steps = args.proc_steps
if proc_steps is None:
    proc_steps = ''
if not proc_steps:
	proc_steps = 'bids'


# Set up working directory
if not os.access(niftidir, os.R_OK):
    os.mkdir(niftidir)
if not os.access(logdir, os.R_OK):
    os.mkdir(logdir)

# set up log file
TIMESTAMP = datetime.datetime.now().strftime("%m%d%y%H%M%S%p")
LOGFILENAME = 'xnatSession_' + TIMESTAMP + '.log'
LOGFILENAME = os.path.join(logdir,LOGFILENAME)
LOGFILE = open(LOGFILENAME,'w+')


# Download and convert Dicoms to BIDS format
if 'bids' in proc_steps:	
    os.chdir(workdir)

    # find step-specific parameters
    step_info=''
    proc_steps_list=proc_steps.split(",");
    for step_item in proc_steps_list:
    	if 'bids:' in step_item:
    		step_info = step_item
    		break
 

    resourceExists = os.listdir(niftidir)
    if not resourceExists or overwrite:
        if overwrite:
        	if session_label == "nosession":
        		dcm2bids_command = "dcm2bids -d {} -p {} -c {} -o {} --clobber".format(dicomdir, subject, dcm2bids_config, niftidir ).split()
        	else:
        		dcm2bids_command = "dcm2bids -d {} -p {} -s {} -c {} -o {} --clobber".format(dicomdir, subject, session_label, dcm2bids_config, niftidir  ).split()
        else:
        	if session_label == "nosession":
        		dcm2bids_command = "dcm2bids -d {} -p {} -c {} -o {}".format(dicomdir, subject, dcm2bids_config, niftidir  ).split()
        	else:
        		dcm2bids_command = "dcm2bids -d {} -p {} -s {} -c {} -o {}".format(dicomdir, subject, session_label, dcm2bids_config, niftidir  ).split()

        logtext(LOGFILE, ' '.join(dcm2bids_command))
        logtext(LOGFILE, str(subprocess.check_output(dcm2bids_command)))
     
        #delete temporary folder
        tmpBidsDir=os.path.join(niftidir,'tmp_dcm2bids')
        if cleanup:
            try:
                logtext(LOGFILE,'Cleaning up %s directory.' % tmpBidsDir)
                rmtree(tmpBidsDir)
            except OSError:
                logtext(LOGFILE, 'problem deleting tmp_dcm2bids directory due to OS error. Please delete manually')


        # perform deface
        createDatasetDescription(niftidir, "PROJECTNAME")
        layout = BIDSLayout(niftidir)

        logtext (LOGFILE,"Get project BIDS bidsaction map")
        if os.path.exists(bidsactionfile):
            with open(bidsactionfile) as f:
            	action = json.load(f)

            try:
            	copyitems = action['copy']
            except KeyError:
            	copyitems = []
            	logtext (LOGFILE, 'No copy items provided.')

            for item in copyitems:
            	entities={}
            	entities['extension']=['nii','nii.gz']
            	try:
            		dataType = item["dataType"]
            		entities['datatype']=dataType
            	except KeyError:
            		dataType = None

            	try:
            		modalityLabel = item["modalityLabel"]
            		entities['suffix']=modalityLabel
            	except KeyError:
            		modalityLabel = None

            	try:
            		customLabels = item["customLabels"]
            		labels = customLabels.split("_")

            		subjectbids=list(filter(lambda x: "sub-" in x, labels))
            		if subjectbids:
            			subjectValue=subjectbids[0].split('-')[1]
            			entities['subject']=subjectValue
            		else:
            			entities['subject']=subject

            		sessionbids=list(filter(lambda x: "ses-" in x, labels))
            		if sessionbids:
            			sessionValue=sessionbids[0].split('-')[1]
            			entities['session']=sessionValue
            		elif session_label != "nosession":
            			entities['session']=session_label

            		task=list(filter(lambda x: "task-" in x, labels))
            		if task:
            			taskValue=task[0].split('-')[1]
            			entities['task']=taskValue

            		acquisition=list(filter(lambda x: "acq-" in x, labels))
            		if acquisition:
            			acquisitionValue=acquisition[0].split('-')[1]
            			entities['acquisition']=acquisitionValue

            		run=list(filter(lambda x: "run-" in x, labels))
            		if run:
            			runValue=run[0].split('-')[1]
            			entities['run']=runValue

            		files = layout.get(return_type='file', **entities)
            		if files:
            			sourcefile = files[0]
            			entities = layout.parse_file_entities(sourcefile)
            			entities['extension'] = 'json'
            			files = layout.get(return_type='file', **entities)
            			if files:
            				sourcejson = files[0]
            			else:
            				sourcejson = None
            		else:
            			sourcefile = None

            	except KeyError:
            		customLabels= None
            		entities['subject']=subject
            		if session_label != "nosession":
            			entities['session']=session_label

            	try:
            		destination = item["destination"]
            	except KeyError:
            		destination = []
            		logtext (LOGFILE, 'No Destination provided for copy')

            	if destination and sourcefile and sourcejson:
            		entities['subject']=subject
            		try:
            			dataType = destination["dataType"]
            			entities['datatype']=dataType
            		except KeyError:
            			dataType = None

            		try:
            			modalityLabel = destination["modalityLabel"]
            			entities['suffix']=modalityLabel
            		except KeyError:
            			modalityLabel = None

            		try:
            			customLabels = destination["customLabels"]
            			labels = customLabels.split("_")

            			sessionbids=list(filter(lambda x: "ses-" in x, labels))
            			if sessionbids:
            				sessionValue=sessionbids[0].split('-')[1]
            				entities['session']=sessionValue

            			task=list(filter(lambda x: "task-" in x, labels))
            			if task:
            				taskValue=task[0].split('-')[1]
            				entities['task']=taskValue
            			else:
            				entities.pop('task', None)

            			acquisition=list(filter(lambda x: "acq-" in x, labels))
            			if acquisition:
            				acquisitionValue=acquisition[0].split('-')[1]
            				entities['acquisition']=acquisitionValue
            			else:
            				entities.pop('acquisition', None)

            			run=list(filter(lambda x: "run-" in x, labels))
            			if run:
            				runValue=run[0].split('-')[1]
            				entities['run']=runValue
            			else:
            				entities.pop('run', None)

            			entities['extension']='nii.gz'
            			outputfile=os.path.join(niftidir, layout.build_path(entities))
            			if os.path.exists(sourcefile):
            				logtext (LOGFILE, "copying %s to %s" %(sourcefile, outputfile))
            				subprocess.check_output(['cp',sourcefile,outputfile])
            			else:
            				logtext (LOGFILE, "ERROR: %s cannot be found. Check bidsaction file logic." % sourcefile)


            			entities['extension']='json'
            			outputjson=os.path.join(niftidir, layout.build_path(entities))
            			if os.path.exists(sourcejson):
            				logtext (LOGFILE, "copying %s to %s" %(sourcejson, outputjson))
            				subprocess.check_output(['cp',sourcejson, outputjson])
            			else:
            				logtext (LOGFILE, "ERROR: %s cannot be found. Check bidsaction file logic." % sourcejson)

            		except KeyError:
            			customLabels= None
            	else:
            		logtext (LOGFILE,"Destination or source file could not be found - skipping") 

        else:
            logtext (LOGFILE,"Could not read project BIDS action file - continuing with upload") 	
        ##########
       
        LOGFILE.flush()
        
    else:
        message = 'Looks like Dcm2bids has already been run. If you want to rerun then set overwrite flag to True.'
        logtext (LOGFILE, message)

logtext (LOGFILE, 'All done with session processing.')

LOGFILE.close()