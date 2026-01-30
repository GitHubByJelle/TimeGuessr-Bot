@description('Location for all resources.')
param location string = resourceGroup().location

@description('Deploy the Container Apps Job. Use false for first deploy (infra only), then true after you pushed the image to ACR.')
param deployJob bool = false

@description('Globally unique ACR name (5-50 lowercase alphanumerics).')
@minLength(5)
@maxLength(50)
param acrName string = toLower('acr${uniqueString(resourceGroup().id)}')

@description('Container Apps managed environment name.')
param environmentName string = 'cae-${uniqueString(resourceGroup().id)}'

@description('Log Analytics workspace name.')
param workspaceName string = 'law-${uniqueString(resourceGroup().id)}'

@description('Container Apps Job name.')
param jobName string = 'my-job'

@description('Image repository name in ACR.')
param imageRepo string = 'timeguessr-bot'

@description('Image tag in ACR.')
param imageTag string = 'latest'

@description('Cron expression (5-field cron: minute hour day month dayOfWeek).')
param cronExpression string = '0 9 * * 1-5' // every weekday at 09:00 AM

@description('Replica timeout in seconds.')
param replicaTimeout int = 1800

@description('CPU cores.')
param cpu string = '0.75'

@description('Memory.')
param memory string = '1.5Gi'


// =======================
// Azure Maps
// =======================
@description('Azure Maps account name.')
param mapsAccountName string = toLower('maps-${uniqueString(resourceGroup().id)}')

resource maps 'Microsoft.Maps/accounts@2025-10-01-preview' = {
  name: mapsAccountName
  location: location
  kind: 'Gen2'
  sku: {
    name: 'G2'
  }
  properties: {
    publicNetworkAccess: 'enabled'
    disableLocalAuth: false
  }
}

var mapsKeys = listKeys(maps.id, maps.apiVersion)


// =======================
// Azure Container Registry (admin creds)
// =======================
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

var acrCreds = listCredentials(acr.id, acr.apiVersion)
var acrServer = acr.properties.loginServer
var acrUsername = acrCreds.username
var acrPassword = acrCreds.passwords[0].value
var image = '${acrServer}/${imageRepo}:${imageTag}'


// =======================
// Log Analytics
// =======================
resource law 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: workspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

var lawKeys = listKeys(law.id, law.apiVersion)


// =======================
// Container Apps Environment
// =======================
resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: lawKeys.primarySharedKey
      }
    }
  }
}


// =======================
// Container Apps Job (Schedule Trigger)
// =======================
resource job 'Microsoft.App/jobs@2024-03-01' = if (deployJob) {
  name: jobName
  location: location
  properties: {
    environmentId: cae.id
    configuration: {
      triggerType: 'Schedule'
      replicaTimeout: replicaTimeout

      secrets: [
        { name: 'acr-pwd', value: acrPassword }
        { name: 'maps-key', value: mapsKeys.primaryKey }

        // app secrets — values NOT defined here
        { name: 'azure-openai-api-key', value: 'placeholder' }
        { name: 'azure-openai-endpoint', value: 'placeholder' }
        { name: 'azure-openai-deployment-name', value: 'placeholder' }
        { name: 'teams-webhook-url', value: 'placeholder' }
      ]

      registries: [
        {
          server: acrServer
          username: acrUsername
          passwordSecretRef: 'acr-pwd'
        }
      ]

      scheduleTriggerConfig: {
        cronExpression: cronExpression
        parallelism: 1
        replicaCompletionCount: 1
      }
    }

    template: {
      containers: [
        {
          name: 'main'
          image: image
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: [
            // Map job secret -> container env var
            { name: 'AZURE_MAPS_KEY', secretRef: 'maps-key' }

            // Map other secrets similarly, e.g.
            { name: 'AZURE_OPENAI_API_KEY', secretRef: 'azure-openai-api-key' }
            { name: 'AZURE_OPENAI_ENDPOINT', secretRef: 'azure-openai-endpoint' }
            { name: 'AZURE_OPENAI_DEPLOYMENT_NAME', secretRef: 'azure-openai-deployment-name' }
            { name: 'TEAMS_WEBHOOK_URL', secretRef: 'teams-webhook-url' }
          ]
        }
      ]
    }
  }
}


// =======================
// Outputs
// =======================
output acrLoginServer string = acrServer
output jobImage string = image
output mapsAccountId string = maps.id
output jobId string = deployJob ? job.id : ''
