datasetId= "" #dataset ID
workspaceId = "" #workspace ID
servicePrincipalId = "" #service principal ID
servicePrincipalSecret = "" #service principal secret
tenantId = "" #tenant ID

rootEndPoint = "https://api.powerbi.com/v1.0/myorg/"

delay = 180 #delay in seconds between each status check API call
batchSize = 4 #number of partitions to refresh in a single batch

payload = {
    "type": "Full",
    "commitMode": "transactional",
    "maxParallelism": 2,
    "retryCount": 1,
    "timeout": "02:00:00",
    "objects": [],
    "applyRefreshPolicy": False
}

