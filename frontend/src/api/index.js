import client from './client';

export const health = {
  get: () => client.apiGet('/health'),
  debug: () => client.apiGet('/debug-test')
};

export const chat = {
  status: () => client.apiGet('/chat')
  , send: (message) => client.apiPost('/message', { message })
};

export const users = {
  status: () => client.apiGet('/users')
};

export const auth = {
  status: () => client.apiGet('/auth')
};

export const handwriting = {
  analyzeImage: async (imageFile, message = null, gradeLevel = null, targetLetter = null) => {
    const formData = new FormData()
    formData.append('image', imageFile)
    if (message) formData.append('message', message)
    if (gradeLevel) formData.append('grade_level', gradeLevel)
    if (targetLetter) formData.append('target_letter', targetLetter)

    const response = await fetch(`${client.API_BASE}/handwriting/analyze-image`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to upload image')
    }

    return response.json()
  },
  analyzeVideo: async (videoFile, message = null, gradeLevel = null, targetLetter = null) => {
    const formData = new FormData()
    formData.append('video', videoFile)
    if (message) formData.append('message', message)
    if (gradeLevel) formData.append('grade_level', gradeLevel)
    if (targetLetter) formData.append('target_letter', targetLetter)

    const response = await fetch(`${client.API_BASE}/handwriting/analyze-video`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to upload video')
    }

    return response.json()
  },
  getAnalysisStatus: (jobId) => client.apiGet(`/handwriting/analysis/${jobId}`),
  getVideoAnalysisStatus: (jobId) => client.apiGet(`/handwriting/video-analysis/${jobId}`)
};

export default { health, chat, users, auth, handwriting };
