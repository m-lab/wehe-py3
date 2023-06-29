'''
#######################################################################################################
#######################################################################################################
Copyright 2018 Northeastern University

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

#######################################################################################################
#######################################################################################################
'''

from python_lib import *

from google.cloud import bigquery
import json, ast

# Wehe results have four datatypes:
ReplayInfo_DATATYPE = 'replayInfo1'
ReplayInfo_SCHEMA = [
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("userID", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("clientIP", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("clientIP2", "STRING"),
    bigquery.SchemaField("replayName", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("extraString", "STRING", description="Extra string sent from the client (not used)"),
    bigquery.SchemaField("historyCount", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("testID", "STRING", mode="REQUIRED",
                         description="Replay type (0 for original and 1 for bit-inverted replay)"),
    bigquery.SchemaField("exception", "STRING", description="The exception if any during the test"),
    bigquery.SchemaField("testFinished", "BOOLEAN"),
    bigquery.SchemaField("testFinishedWoutError", "BOOLEAN"),
    bigquery.SchemaField("iperfInfo", "STRING"),
    bigquery.SchemaField("testDurationServer", "FLOAT", description="Test length (in seconds) recorded on the server"),
    bigquery.SchemaField("testDurationClient", "FLOAT", description="Test length (in seconds) recorded on the client"),
    bigquery.SchemaField("metadata", "RECORD", fields=[
        bigquery.SchemaField("cellInfo", "STRING"),
        bigquery.SchemaField("model", "STRING"),
        bigquery.SchemaField("manufacturer", "STRING"),
        bigquery.SchemaField("carrierName", "STRING"),
        bigquery.SchemaField("os", "RECORD", fields=[
            bigquery.SchemaField("INCREMENTAL", "INTEGER"),
            bigquery.SchemaField("RELEASE", "STRING"),
            bigquery.SchemaField("SDK_INT", "INTEGER"),
        ]),
        bigquery.SchemaField("networkType", "STRING"),
        bigquery.SchemaField("locationInfo", "RECORD", fields=[
            bigquery.SchemaField("latitude", "FLOAT"),
            bigquery.SchemaField("longitude", "FLOAT"),
            bigquery.SchemaField("country", "STRING"),
            bigquery.SchemaField("countryCode", "STRING"),
            bigquery.SchemaField("city", "STRING"),
            bigquery.SchemaField("localTime", "TIMESTAMP"),
        ]),
        bigquery.SchemaField("updatedCarrierName", "STRING"),
    ]),
    bigquery.SchemaField("emptyBool", "BOOLEAN", description="A Boolean value no longer used"),
    bigquery.SchemaField("clientVersion", "STRING", description="The version of client app"),
    bigquery.SchemaField("measurementUUID", "STRING", description="Unique measurement identifier")
]

ClientXputs_DATATYPE = 'clientXputs1'
ClientXputs_SCHEMA = [
    bigquery.SchemaField("userID", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("historyCount", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("testID", "STRING", mode="REQUIRED",
                         description="Replay type (0 for original and 1 for bit-inverted replay)"),
    bigquery.SchemaField("xputSamples", "FLOAT", mode="REPEATED", description="throughput samples collected at client"),
    bigquery.SchemaField("intervals", "FLOAT", mode="REPEATED",
                         description="time intervals at which the throughput samples are recorded"),
]

Decisions_DATATYPE = 'decisions1'
Decisions_SCHEMA = [
    bigquery.SchemaField("userID", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("historyCount", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("testID", "STRING", mode="REQUIRED",
                         description="Replay type (0 for original and 1 for bit-inverted replay)"),
    bigquery.SchemaField("avgXputDiffPct", "FLOAT",
                         description="avgXputDiff / max(control's avgXput, original's avgXput)"),
    bigquery.SchemaField("KSAcceptRatio", "FLOAT", description="KS test acceptance ratio"),
    bigquery.SchemaField("avgXputDiff", "FLOAT", description="control's avgXput - original's avgXput"),
    bigquery.SchemaField("emptyField", "STRING", description="not used anymore"),
    bigquery.SchemaField("originalXputStats", "RECORD", fields=[
        bigquery.SchemaField("max", "FLOAT"),
        bigquery.SchemaField("min", "FLOAT"),
        bigquery.SchemaField("average", "FLOAT"),
        bigquery.SchemaField("median", "FLOAT"),
        bigquery.SchemaField("std", "FLOAT"),
    ]),
    bigquery.SchemaField("controlXputStats", "RECORD", fields=[
        bigquery.SchemaField("max", "FLOAT"),
        bigquery.SchemaField("min", "FLOAT"),
        bigquery.SchemaField("average", "FLOAT"),
        bigquery.SchemaField("median", "FLOAT"),
        bigquery.SchemaField("std", "FLOAT"),
    ]),
    bigquery.SchemaField("minXput", "FLOAT"),
    bigquery.SchemaField("KSAvgDVal", "FLOAT", description="Average D value of the sampled KS test"),
    bigquery.SchemaField("KSAvgPVal", "FLOAT", description="Average P value of the sampled KS test"),
    bigquery.SchemaField("KSDVal", "FLOAT", description="D value of the KS test"),
    bigquery.SchemaField("KSPVal", "FLOAT", description="P value of the KS test"),
]


def get_datatype_results_folder(datatype):
    results_folder = os.path.join(Configs().get('mainPath'), datatype, time.strftime("%Y/%m/%d", time.gmtime()))
    os.makedirs(results_folder, exist_ok=True)
    return results_folder


# Methods that create + save the schema files
def create_replayInfo_schema():
    schemaFile = os.path.join(Configs().get('bqSchemaFolder'), '{}.json'.format(ReplayInfo_DATATYPE))
    with open(schemaFile, 'w') as f:
        f.write(json.dumps([field.to_api_repr() for field in ReplayInfo_SCHEMA]))


def create_clientXputs_schema():
    schemaFile = os.path.join(Configs().get('bqSchemaFolder'), '{}.json'.format(ClientXputs_DATATYPE))
    with open(schemaFile, 'w') as f:
        f.write(json.dumps([field.to_api_repr() for field in ClientXputs_SCHEMA]))


def create_decisions_schema():
    schemaFile = os.path.join(Configs().get('bqSchemaFolder'), '{}.json'.format(Decisions_DATATYPE))
    with open(schemaFile, 'w') as f:
        f.write(json.dumps([field.to_api_repr() for field in Decisions_SCHEMA]))


# Copy files from temporary to permanent directory
# TODO: currenlty we only copy the files (after full transision to jostler change operation to move)
def move_replayInfo(userID, historyCount, testID):
    tmpReplayInfoFile = '{}/{}/replayInfo/replayInfo_{}_{}_{}.json'.format(
        Configs().get('tmpResultsFolder'), userID, userID, historyCount, testID
    )
    permReplayInfoFile = '{}/replayInfo_{}_{}_{}.json'.format(
        get_datatype_results_folder(ReplayInfo_DATATYPE), userID.replace('@', ' '), historyCount, testID
    )

    with open(tmpReplayInfoFile, 'r') as readFile:
        info = json.load(readFile)

    info_key_value = {k.name: v for k, v in zip(ReplayInfo_SCHEMA, info)}
    try:
        info_key_value['metadata'] = ast.literal_eval(info_key_value['metadata'])
    except:
        info_key_value['metadata'] = None

    with open(permReplayInfoFile, 'w') as f:
        f.write(json.dumps(info_key_value))


def move_clientXputs(userID, historyCount, testID):
    tmpClientXputsFile = '{}/{}/clientXputs/Xput_{}_{}_{}.json'.format(
        Configs().get('tmpResultsFolder'), userID, userID, historyCount, testID
    )
    permClientXputsFile = '{}/Xput_{}_{}_{}.json'.format(
        get_datatype_results_folder(ClientXputs_DATATYPE), userID.replace('@', ' '), historyCount, testID
    )

    with open(tmpClientXputsFile, 'r') as readFile:
        xputs = json.load(readFile)

    xputs_key_value = {
        'userID': userID, 'historyCount': historyCount, 'testID': testID, 'xputSamples': xputs[0], 'intervals': xputs[1]
    }
    with open(permClientXputsFile, 'w') as f:
        f.write(json.dumps(xputs_key_value))


def move_result_file(userID, historyCount, testID):
    tmpDecisionsFile = '{}/{}/decisions/results_{}_Client_{}_{}.json'.format(
        Configs().get('tmpResultsFolder'), userID, userID, historyCount, testID
    )
    permDecisionsFile = '{}/results_{}_Client_{}_{}.json'.format(
        get_datatype_results_folder(Decisions_DATATYPE), userID.replace('@', ' '), historyCount, testID
    )

    with open(tmpDecisionsFile, 'r') as readFile:
        results = json.load(readFile)

    results = [userID, historyCount, testID] + results
    results_key_value = {k.name: v for k, v in zip(Decisions_SCHEMA, results)}

    key_stats = ['max', 'min', 'average', 'median', 'std']
    results_key_value['originalXputStats'] = {k: v for k, v in zip(key_stats, results_key_value['originalXputStats'])}
    results_key_value['controlXputStats'] = {k: v for k, v in zip(key_stats, results_key_value['controlXputStats'])}

    with open(permDecisionsFile, 'w') as f:
        f.write(json.dumps(results_key_value))

