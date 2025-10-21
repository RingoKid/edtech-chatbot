import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Edit, 
  Trash2, 
  Plus, 
  Save, 
  X, 
  Eye, 
  Search,
  Filter,
  RefreshCw,
  FileText,
  AlertCircle
} from 'lucide-react'
import CreateFormModal from '../components/CreateFormModal'

const AdminPortal = () => {
  const [forms, setForms] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedForm, setSelectedForm] = useState(null)
  const [isEditing, setIsEditing] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterDomain, setFilterDomain] = useState('all')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingContent, setEditingContent] = useState('')
  const [editingTitle, setEditingTitle] = useState('')

  // Form categories
  const domains = {
    handwriting: 'Handwriting & Spelling',
    vocabulary: 'Vocabulary & Syntax', 
    ideas: 'Idea Generation',
    general: 'General'
  }

  // Fetch all forms
  const fetchForms = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/v1/forms')
      if (!response.ok) throw new Error('Failed to fetch forms')
      const data = await response.json()
      setForms(data.forms)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Update form
  const updateForm = async (formId, title, content) => {
    try {
      const response = await fetch(`/api/v1/forms/${formId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          content: JSON.parse(content)
        })
      })
      
      if (!response.ok) throw new Error('Failed to update form')
      
      // Refresh forms list
      await fetchForms()
      setIsEditing(false)
      setSelectedForm(null)
    } catch (err) {
      setError(err.message)
    }
  }

  // Delete form
  const deleteForm = async (formId) => {
    if (!window.confirm('Are you sure you want to delete this form?')) return
    
    try {
      const response = await fetch(`/api/v1/forms/${formId}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) throw new Error('Failed to delete form')
      
      // Refresh forms list
      await fetchForms()
      if (selectedForm?.form_id === formId) {
        setSelectedForm(null)
        setIsEditing(false)
      }
    } catch (err) {
      setError(err.message)
    }
  }

  // Handle edit
  const handleEdit = (form) => {
    setSelectedForm(form)
    setEditingTitle(form.title)
    setEditingContent(JSON.stringify(form.content, null, 2))
    setIsEditing(true)
  }

  // Handle save
  const handleSave = () => {
    try {
      const parsedContent = JSON.parse(editingContent)
      updateForm(selectedForm.form_id, editingTitle, editingContent)
    } catch (err) {
      setError('Invalid JSON format in content')
    }
  }

  // Handle cancel
  const handleCancel = () => {
    setIsEditing(false)
    setSelectedForm(null)
    setEditingContent('')
    setEditingTitle('')
  }

  // Create form
  const createForm = async (formData) => {
    try {
      const response = await fetch('/api/v1/forms', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })
      
      if (!response.ok) throw new Error('Failed to create form')
      
      // Refresh forms list
      await fetchForms()
      setShowCreateForm(false)
    } catch (err) {
      setError(err.message)
    }
  }

  // Filter forms
  const filteredForms = forms.filter(form => {
    const matchesSearch = form.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         form.category.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesDomain = filterDomain === 'all' || form.domain === filterDomain
    return matchesSearch && matchesDomain
  })

  useEffect(() => {
    fetchForms()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading forms...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Admin Portal</h1>
              <p className="text-gray-600">Manage educational forms and content</p>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Form
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Forms List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border">
              {/* Search and Filter */}
              <div className="p-4 border-b">
                <div className="space-y-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                      type="text"
                      placeholder="Search forms..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <select
                    value={filterDomain}
                    onChange={(e) => setFilterDomain(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="all">All Domains</option>
                    {Object.entries(domains).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Forms List */}
              <div className="max-h-96 overflow-y-auto">
                {filteredForms.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p>No forms found</p>
                  </div>
                ) : (
                  filteredForms.map((form) => (
                    <motion.div
                      key={form.form_id}
                      whileHover={{ scale: 1.02 }}
                      className={`p-4 border-b cursor-pointer transition-colors ${
                        selectedForm?.form_id === form.form_id
                          ? 'bg-blue-50 border-blue-200'
                          : 'hover:bg-gray-50'
                      }`}
                      onClick={() => setSelectedForm(form)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900 truncate">
                            {form.title}
                          </h3>
                          <p className="text-sm text-gray-500">
                            Form {form.category} • {domains[form.domain] || form.domain}
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            Updated: {new Date(form.updated_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex gap-1 ml-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleEdit(form)
                            }}
                            className="p-1 text-gray-400 hover:text-blue-600"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteForm(form.form_id)
                            }}
                            className="p-1 text-gray-400 hover:text-red-600"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Form Editor */}
          <div className="lg:col-span-2">
            {selectedForm ? (
              <div className="bg-white rounded-lg shadow-sm border">
                {/* Form Header */}
                <div className="p-4 border-b">
                  <div className="flex justify-between items-start">
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900">
                        {isEditing ? 'Edit Form' : 'View Form'}
                      </h2>
                      <p className="text-sm text-gray-500">
                        Form {selectedForm.category} • {domains[selectedForm.domain] || selectedForm.domain}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {isEditing ? (
                        <>
                          <button
                            onClick={handleSave}
                            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
                          >
                            <Save className="w-4 h-4" />
                            Save
                          </button>
                          <button
                            onClick={handleCancel}
                            className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 flex items-center gap-2"
                          >
                            <X className="w-4 h-4" />
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => handleEdit(selectedForm)}
                          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
                        >
                          <Edit className="w-4 h-4" />
                          Edit
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Form Content */}
                <div className="p-4">
                  {isEditing ? (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Title
                        </label>
                        <input
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Content (JSON)
                        </label>
                        <textarea
                          value={editingContent}
                          onChange={(e) => setEditingContent(e.target.value)}
                          rows={20}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                          {selectedForm.title}
                        </h3>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                            {JSON.stringify(selectedForm.content, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
                <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Select a form to view or edit
                </h3>
                <p className="text-gray-500">
                  Choose a form from the list to view its content or make edits
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Form Modal */}
      <CreateFormModal
        isOpen={showCreateForm}
        onClose={() => setShowCreateForm(false)}
        onSubmit={createForm}
      />
    </div>
  )
}

export default AdminPortal
