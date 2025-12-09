// CivicNav Infrastructure - Main Bicep Template
// Orchestrates Azure OpenAI, AI Search, and Container Apps deployment

targetScope = 'resourceGroup'

@minLength(1)
@maxLength(64)
@description('Name of the environment (e.g., dev, staging, prod)')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string = resourceGroup().location

@description('Name of the Azure OpenAI resource')
param openAiName string = ''

@description('Name of the Azure AI Search resource')
param searchName string = ''

@description('Name of the Container App')
param containerAppName string = ''

@description('Container image to deploy')
param containerImage string = ''

// Generate unique names if not provided
var abbrs = {
  openAi: 'oai'
  search: 'srch'
  containerApp: 'ca'
  containerEnv: 'cae'
  registry: 'cr'
  logAnalytics: 'log'
}

var resourceToken = toLower(uniqueString(resourceGroup().id, environmentName, location))
var tags = {
  'azd-env-name': environmentName
  'civicnav-lab': 'true'
}

// Azure OpenAI
module openAi 'modules/openai.bicep' = {
  name: 'openai'
  params: {
    name: !empty(openAiName) ? openAiName : '${abbrs.openAi}-${resourceToken}'
    location: location
    tags: tags
  }
}

// Azure AI Search
module search 'modules/search.bicep' = {
  name: 'search'
  params: {
    name: !empty(searchName) ? searchName : '${abbrs.search}-${resourceToken}'
    location: location
    tags: tags
  }
}

// Container Apps Environment and App
module containerApp 'modules/containerapp.bicep' = {
  name: 'containerapp'
  params: {
    name: !empty(containerAppName) ? containerAppName : '${abbrs.containerApp}-${resourceToken}'
    location: location
    tags: tags
    containerImage: containerImage
    openAiEndpoint: openAi.outputs.endpoint
    searchEndpoint: search.outputs.endpoint
    searchIndexName: 'civicnav-index'
    openAiPrincipalId: openAi.outputs.principalId
    searchPrincipalId: search.outputs.principalId
  }
}

// Outputs for azd
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId

output AZURE_OPENAI_ENDPOINT string = openAi.outputs.endpoint
output AZURE_OPENAI_NAME string = openAi.outputs.name

output AZURE_SEARCH_ENDPOINT string = search.outputs.endpoint
output AZURE_SEARCH_NAME string = search.outputs.name
output AZURE_SEARCH_INDEX string = 'civicnav-index'

output CONTAINER_APP_NAME string = containerApp.outputs.name
output CONTAINER_APP_URL string = containerApp.outputs.url
output CONTAINER_APP_IDENTITY_PRINCIPAL_ID string = containerApp.outputs.identityPrincipalId
