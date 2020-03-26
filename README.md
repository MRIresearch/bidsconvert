# bidsconvert
Docker image for converting DICOMS to BIDS format using dcm2bids version 2.1.4 (https://cbedetti.github.io/Dcm2Bids/)

# Usage of Bidsconvert.py
Open a terminal and run docker image as shown further below to convert dicoms in $PWD/DICOM to BIDS format in $PWD/nifti using the helper python program `bidsconvert.py`. 
This example creates bids files for subject `106` and for a session `post` thus creating the folder structure sub-106 -> ses-post ->
The BIDS configuration file is passed using --bidsconfig
Additionally a bids action file can also be passed - this is not part of the dcm2bids ecosystem and provides a means of copying files once they have been created to other folders within the bids structure. This functionality is under construction and provides support for copy operations only at the moment. 


`docker pull orbisys/bidsconvert:0.2`
`docker run  --rm -v $PWD:/mnt                \ 
                  -v $PWD/DICOM:/dicom        \
                  -v $PWD/nifti:/nifti        \
                  orbisys/bidsconvert:0.2     \   
                  python /src/bidsconvert.py  \ 
                  --subject 106 --session_label post --dicomdir /dicom --niftidir /nifti --bidsconfig /mnt/dcm2bids_config.json --bidsaction /mnt/dcm2bids_actions.json --overwrite True`


# Usage of dcm2bids and dcm2niix directly
Alternatively users can ignore bidsconvert.py and directly call dcm2bids or dcm2niix directly within the container. Simply replace bidsconvert.py in the commad call above with the command you prefer instead.

`docker run  --rm -v $PWD:/mnt                \
                  -v $PWD/DICOM:/dicom        \
                  -v $PWD/nifti:/nifti        \
                  orbisys/bidsconvert:0.2     \
                  dcm2bids --help`

`docker run  --rm -v $PWD:/mnt                \
                  -v $PWD/DICOM:/dicom        \
                  -v $PWD/nifti:/nifti        \
                  orbisys/bidsconvert:0.2     \
                  dcm2niix`

# bidsaction file
The bidsaction file allos for simple copying operation using a json file format that is very similar to the dcm2bids configuration file. For example this configuration file: 

`{
    "copy": [
        {
        "dataType": "func",
        "modalityLabel": "bold",
        "customLabels": "task-rest",
        "destination": {
            "modalityLabel": "sbref",
            "customLabels": "task-dummy"
            }
        },
        {
        "dataType": "anat",
        "modalityLabel": "T1w",
        "destination": {
            "modalityLabel": "FLAIR",
            "customLabels": "acq-nd"
            }
        }
		
    ]
}`

Will end up copying functional files called $SUB_task-rest_bold to $SUB_task-dummy_sbref
and also copying anatomical files called $SUB_T1w to $SUB_acq-nd_FLAIR
