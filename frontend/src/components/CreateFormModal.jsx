import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Plus, AlertCircle, Code, Edit3 } from 'lucide-react'
import FormBuilder from './FormBuilder'

const CreateFormModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    category: '',
    title: '',
    content: {}
  })
  const [error, setError] = useState('')
  const [useFormBuilder, setUseFormBuilder] = useState(true)
  const [jsonContent, setJsonContent] = useState('{\n  \n}')

  const categories = [
    { value: 'handwriting', label: 'Handwriting & Spelling' },
    { value: 'vocabulary', label: 'Vocabulary & Syntax' },
    { value: 'ideas', label: 'Idea Organization and Generation' }
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // Validate required fields
    if (!formData.category || !formData.title) {
      setError('Please fill in all required fields')
      return
    }

    let contentToSubmit

    if (useFormBuilder) {
      // Use form builder data
      if (!formData.content || Object.keys(formData.content).length === 0) {
        setError('Please add at least one field to the form content')
        return
      }
      // Wrap content in form key structure
      // Use category-based key: form_handwriting, form_vocabulary, form_ideas
      // Or use generic form_data if category doesn't match pattern
      const categoryToKey = {
        'handwriting': 'form_handwriting',
        'vocabulary': 'form_vocabulary', 
        'ideas': 'form_ideas'
      }
      const formKey = categoryToKey[formData.category] || 'form_data'
      contentToSubmit = {
        [formKey]: formData.content
      }
    } else {
      // Use JSON editor
      try {
        contentToSubmit = JSON.parse(jsonContent)
      } catch (err) {
        setError('Invalid JSON format in content field')
        return
      }
    }

    try {
      await onSubmit({
        category: formData.category,
        title: formData.title,
        content: contentToSubmit
      })
      
      // Reset form
      setFormData({
        category: '',
        title: '',
        content: {}
      })
      setJsonContent('{\n  \n}')
      onClose()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleClose = () => {
    setFormData({
      category: '',
      title: '',
      content: {}
    })
    setJsonContent('{\n  \n}')
    setError('')
    onClose()
  }

  const handleFormBuilderChange = (newContent) => {
    setFormData({ ...formData, content: newContent })
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={handleClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-xl font-semibold text-gray-900">Create New Form</h2>
              <button
                onClick={handleClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
              <div className="p-6 space-y-6 flex-1 overflow-y-auto">
                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-red-600" />
                    <p className="text-red-800">{error}</p>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Category *
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select a category</option>
                    {categories.map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Title *
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter form title"
                    required
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Content *
                    </label>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setUseFormBuilder(true)}
                        className={`flex items-center gap-1 px-3 py-1 rounded text-sm transition-colors ${
                          useFormBuilder
                            ? 'bg-blue-100 text-blue-700 border border-blue-300'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        <Edit3 className="w-3 h-3" />
                        Form Builder
                      </button>
                      <button
                        type="button"
                        onClick={() => setUseFormBuilder(false)}
                        className={`flex items-center gap-1 px-3 py-1 rounded text-sm transition-colors ${
                          !useFormBuilder
                            ? 'bg-blue-100 text-blue-700 border border-blue-300'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        <Code className="w-3 h-3" />
                        JSON Editor
                      </button>
                    </div>
                  </div>
                  
                  {useFormBuilder ? (
                    <FormBuilder
                      value={formData.content}
                      onChange={handleFormBuilderChange}
                    />
                  ) : (
                    <>
                      <textarea
                        value={jsonContent}
                        onChange={(e) => setJsonContent(e.target.value)}
                        rows={15}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                        placeholder='{"form_key": {"title": "Example", "description": "..."}}'
                        required
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Enter valid JSON content for the form
                      </p>
                    </>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Create Form
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default CreateFormModal
