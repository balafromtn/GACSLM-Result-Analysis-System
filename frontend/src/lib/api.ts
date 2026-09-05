import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

export async function uploadStudentCsv(workspaceName: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);

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

export async function getWorkspaceSubjects(workspaceId: string | number) {
  const encodedId = encodeURIComponent(workspaceId.toString());
  const response = await apiClient.get(`/analytics/${encodedId}/subjects`);
  return response.data;
}

export async function getWorkspaceDistribution(workspaceId: string | number) {
  const encodedId = encodeURIComponent(workspaceId.toString());
  const response = await apiClient.get(`/analytics/${encodedId}/distribution`);
  return response.data;
}

export async function getWorkspaceInsights(workspaceId: string | number) {
  const encodedId = encodeURIComponent(workspaceId.toString());
  const response = await apiClient.get(`/analytics/${encodedId}/insights`);
  return response.data;
}

export async function getStudentDetails(studentId: string | number) {
  const response = await apiClient.get(`/analytics/student/${studentId}`);
  return response.data;
}

export async function getPassFailDistribution(workspaceId: string | number) {
  const encodedId = encodeURIComponent(workspaceId.toString());
  const response = await apiClient.get(`/analytics/${encodedId}/pass-fail`);
  return response.data;
}

export async function getGenderPerformance(workspaceId: string | number) {
  const encodedId = encodeURIComponent(workspaceId.toString());
  const response = await apiClient.get(`/analytics/${encodedId}/gender-performance`);
  return response.data;
}

export async function getScrapingStatus(workspaceId: string) {
  const response = await apiClient.get(`/workspace/${encodeURIComponent(workspaceId)}/status`);
  return response.data;
}

export async function getCommunityPerformance(workspaceId: string | number) {
  const encodedId = encodeURIComponent(workspaceId.toString());
  const response = await apiClient.get(`/analytics/${encodedId}/community`);
  return response.data;
}

export async function getWorkspaceChat(workspaceId: string | number, query: string) {
  const encodedId = encodeURIComponent(workspaceId.toString());
  const response = await apiClient.post(`/analytics/${encodedId}/chat`, { query });
  return response.data;
}