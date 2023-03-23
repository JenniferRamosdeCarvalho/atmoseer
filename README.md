# AtmoSeer

## About

This project provides a pipeline to build rainfall forecast models using 1D Convolutional Neural Networks. The pipeline can be configured with different meteorological data sources.

## Install

In the root directory of this repository, type the following command (you must have conda installed in your system):

./setup.sh

## Application

### Execution
The project has 3 types of scripts that can be executed, Data Import, Pre-processing and Model Generation. To access the codes it is necessary to be in the `./src` directory.

#### Data Import
In the project there are 3 different data import scripts, for COR stations, INMET stations and Radiosonde. They are responsible for generating the datasets that will be used for training the nowcasting model.

Script **_estacoes_cor.py_** has four command line arguments:

- `-s` or `--sta` that define which station will be selected. You have to provide the weather station of interest by name: alto_da_boa_vista, guaratiba, iraja, jardim_botanico, riocentro, santa_cruz, sao_cristovao, vidigal. 
- `-a` or `--all` which if filled with 1 indicates that they will be importing the data of all stations.
- `-b` or `--begin` and `-e` or `--end` which can be filled with the interval of years for importing the data (The default interval for data import period is from 1997 to 2022). 

Example 1:

`python estacoes_cor.py -s são_cristovao`

The above command imports the São Cristóvão station dataset into the project data folder.

Example 2:

`python estacoes_cor.py -a 1 -b 2000 -e 2015`

The above command imports all the stations in the period from 2000 to 2015.


Script **_estacoes_inmet.py_** has four command line arguments:

-  `-s` or `--sta`, which defines which station will be selected. You must provide the weather stations using their code. The possible codes are A652 (Forte de Copacabana), A636 (Jacarepagua), A621 (Vila Militar), A602 (Marambaia).
- `-a` or `--all` which if filled with 1 indicates that data from all stations will be imported.
- `-b` or `--begin` and `-e` or `--end` which can be filled with the interval of years for importing the data (The default interval for data import period is from 1997 to 2022).

Example 1:

`Python stations_inmet.py -s A652`

The data set for the Copacabana Fort station will be imported into the project data folder.

Example 2:

`Python estacoes_inmet.py -a 1 -b 1999 -e 2017`

The datasets of all stations in the period from 1999 to 2017 will be imported.


**_estacoes_rad.py_** has two command line arguments:
- `-b` or `--begin` and `-e` or `--end` which can be filled in with the year interval for data import (The default interval for data import period is from 1997 to 2022). 

When running it the Galeão Airport radiosonde dataset will be generated.

Example:

`python stations_rad.py`

The above command imports Galeão Airport radiosonde (SGBL) observations into the project data folder.

Script **_index_rad.py_** has no arguments, when running it will generate the atmospheric instability indexes for the data imported in the script **_estacoes_rad.py_**.

Example:

`python index_rad.py`

Data from the Galeão Airport radiosonde will be used to calculate atmospheric instability indexes, generating a new dataset in the project's data folder.

All datasets generated by the above scrpts will be stored in the `./data` folder.


#### Pre Processing
The preprocessing script is responsible for performing several operations on the original dataset, such as creating variables or aggregating data, which can be interesting for model training and its final result. To run the preprocessing script you need to run the `Python pre_processing.py` command. The pre_processing code has 3 possible arguments, with only the first being required.

The arguments are:
 - `-f` or `--file` Mandatory argument, represents the name of the data file that will be used as a base for the model. It must be the same as the name of one of the files present in the *Data* folder of the project.
 - `-d` or `--data` Defines the data sources that will be used to assemble the dataset.
  Uses the format of defined acronyms in the text
    - E : Weather station only
    - E-N : Weather station and numerical model
    - E-R : Weather station and radiosonde
    - E-N-R : Weather station, numerical model and radiosonde
- `-s` or `--sta` Defines how many nearby stations will be added to the dataset
Execution Example:
  
  `Python pre_processing.py -f 'RIO DE JANEIRO - FORTE DE COPACABANA_1997_2022' -d 'E-N-R' -s 5'`

A dataset will be created from the Forte de Copacabana station, with the aggregation of data from the 5 nearest meteorological stations, using the data sources: numerical model and radiosonde.


#### Model generation
The model generation script is responsible for performing the training and exporting the results obtained by the model after testing. It can be executed through the command `Python creates_modelo.py`, which needs two arguments `-f` or `-file` which receives the name of one of the datasets generated from pre-processing and `-r` or ` --reg` which defines the architecture that will be used.
Execution Example:

`Python creates_modelo.py -f 'RIO DE JANEIRO - FORTE DE COPACABANA_E-N-R_EI+5NN'`

An ordinal classification model will be created based on the already processed dataset from the Forte de Copacabana station.

`Python creates_modelo.py -f 'RIO DE JANEIRO - FORTE DE COPACABANA_E-N-R_EI+5NN' -r 1`

A regression model will be created based on the already processed data set of the Forte de Copacabana station

## System test example

Import : `Python estacoes_inmet.py -s A652`

Pre processing : `Python pre_processing.py -f 'RIO DE JANEIRO - FORTE DE COPACABANA' -d 'E-N-R' -s 5 `

Model generation : `Python creates_modelo.py -f 'RIO DE JANEIRO - FORTE DE COPACABANA_E-N-R_EI+5NN' -r 1`
