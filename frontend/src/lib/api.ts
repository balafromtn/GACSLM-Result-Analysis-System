import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

export async function uploadStudentCsv(workspaceName: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);

  // Send workspace_name as a query parameter (?workspace_name=...) to match FastAPI
  const response = await apiClient.post(`/upload?workspace_name=${encodeURIComponent(workspaceName)}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
}

export async function getWorkspaceSummary(workspaceId: string | number) {
  const encodedId = encodeURIComponent(workspaceId.toString());
  const response = await apiClient.get(`/analytics/${encodedId}/summary`);
  return response.data;
}

export async function getWorkspaceStudents(workspaceId: string | number) {
  const encodedId = encodeURIComponent(workspaceId.toString());
  const response = await apiClient.get(`/analytics/${encodedId}/students`);
  return response.data;
}