import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Plus, Trash2, ChevronDown, ChevronRight, Type, List, Folder } from 'lucide-react'

/**
 * Form Builder Component - Allows building JSON structure through key-value pairs
 */
const FormBuilder = ({ value, onChange }) => {
  const [data, setData] = useState(value || {})
  const debounceTimerRef = useRef(null)
  const pendingUpdateRef = useRef(null)

  // Debounced update function
  const updateData = useCallback((newData) => {
    // Update local state immediately for UI responsiveness
    setData(newData)
    
    // Store pending update
    pendingUpdateRef.current = newData
    
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    
    // Debounce the parent update
    debounceTimerRef.current = setTimeout(() => {
      if (pendingUpdateRef.current) {
        onChange(pendingUpdateRef.current)
        pendingUpdateRef.current = null
      }
    }, 300) // 300ms debounce
  }, [onChange])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
      // Flush any pending updates on unmount
      if (pendingUpdateRef.current) {
        onChange(pendingUpdateRef.current)
      }
    }
  }, [onChange])

  const addField = (parentPath = '') => {
    const newData = { ...data }
    const newKey = `new_field_${Date.now()}`
    
    if (parentPath) {
      const keys = parentPath.split('.')
      let current = newData
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = {}
        current = current[keys[i]]
      }
      current[keys[keys.length - 1]] = { ...current[keys[keys.length - 1]], [newKey]: '' }
    } else {
      newData[newKey] = ''
    }
    
    updateData(newData)
  }

  const updateField = (path, key, newKey, newValue, valueType) => {
    const newData = { ...data }
    const keys = path ? path.split('.') : []
    
    let current = newData
    for (const k of keys) {
      current = current[k]
    }
    
    // Convert value based on type
    let processedValue = newValue
    if (valueType === 'number') {
      processedValue = newValue === '' ? 0 : Number(newValue)
    } else if (valueType === 'boolean') {
      processedValue = newValue === 'true'
    } else if (valueType === 'array') {
      // If it's a string, try to parse as JSON array, otherwise split by comma
      try {
        processedValue = JSON.parse(newValue)
      } catch {
        processedValue = newValue.split(',').map(item => item.trim()).filter(item => item)
      }
    } else if (valueType === 'object') {
      // Keep as object if it already is, otherwise create empty object
      if (typeof newValue === 'object' && newValue !== null) {
        processedValue = newValue
      } else {
        processedValue = {}
      }
    }
    
    // If key changed, delete old and add new
    if (key !== newKey) {
      delete current[key]
    }
    
    current[newKey] = processedValue
    updateData(newData)
  }

  const deleteField = (path, key) => {
    const newData = { ...data }
    const keys = path ? path.split('.') : []
    
    if (keys.length === 0) {
      delete newData[key]
    } else {
      let current = newData
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]]
      }
      delete current[keys[keys.length - 1]][key]
    }
    
    updateData(newData)
  }

  const FieldEditor = ({ fieldKey, fieldValue, path = '', level = 0, fieldId }) => {
    const [isExpanded, setIsExpanded] = useState(level < 2)
    
    // Use refs to store current values - these don't trigger re-renders
    const keyRef = useRef(fieldKey)
    const valueRef = useRef(
      typeof fieldValue === 'object' && fieldValue !== null && !Array.isArray(fieldValue)
        ? ''
        : Array.isArray(fieldValue)
        ? JSON.stringify(fieldValue)
        : String(fieldValue)
    )
    const [valueType, setValueType] = useState(
      typeof fieldValue === 'object' && fieldValue !== null
        ? Array.isArray(fieldValue)
          ? 'array'
          : 'object'
        : typeof fieldValue === 'number'
        ? 'number'
        : typeof fieldValue === 'boolean'
        ? 'boolean'
        : 'string'
    )

    // Local state only for rendering - synced from refs
    const [localKey, setLocalKey] = useState(fieldKey)
    const [localValue, setLocalValue] = useState(valueRef.current)

    // Debounce timer for parent updates
    const updateTimerRef = useRef(null)
    const isUpdatingRef = useRef(false)

    // Sync refs when props change externally (only if not currently updating)
    useEffect(() => {
      if (!isUpdatingRef.current) {
        keyRef.current = fieldKey
        valueRef.current = typeof fieldValue === 'object' && fieldValue !== null && !Array.isArray(fieldValue)
          ? ''
          : Array.isArray(fieldValue)
          ? JSON.stringify(fieldValue)
          : String(fieldValue)
        setLocalKey(fieldKey)
        setLocalValue(valueRef.current)
      }
      isUpdatingRef.current = false
    }, [fieldKey, fieldValue])

    // Function to update parent (debounced)
    const scheduleParentUpdate = useCallback(() => {
      if (updateTimerRef.current) {
        clearTimeout(updateTimerRef.current)
      }
      updateTimerRef.current = setTimeout(() => {
        isUpdatingRef.current = true
        updateField(path, fieldKey, keyRef.current, valueRef.current, valueType)
      }, 500) // Longer debounce - 500ms
    }, [path, fieldKey, valueType])

    const isObject = typeof fieldValue === 'object' && fieldValue !== null && !Array.isArray(fieldValue)
    const isArray = Array.isArray(fieldValue)

    const handleValueChange = (newValue) => {
      // Update ref immediately (no re-render)
      valueRef.current = newValue
      // Update local state for display
      setLocalValue(newValue)
      // Schedule parent update (debounced)
      scheduleParentUpdate()
    }

    const handleKeyChange = (newKey) => {
      // Update ref immediately (no re-render)
      keyRef.current = newKey
      // Update local state for display
      setLocalKey(newKey)
      // Schedule parent update (debounced)
      scheduleParentUpdate()
    }

    // Cleanup timer on unmount
    useEffect(() => {
      return () => {
        if (updateTimerRef.current) {
          clearTimeout(updateTimerRef.current)
        }
      }
    }, [])

    const handleTypeChange = (newType) => {
      isUpdatingRef.current = true
      setValueType(newType)
      let defaultValue = ''
      if (newType === 'number') defaultValue = '0'
      else if (newType === 'boolean') defaultValue = 'true'
      else if (newType === 'array') defaultValue = '[]'
      else if (newType === 'object') {
        updateField(path, fieldKey, localKey, {}, newType)
        return
      }
      setLocalValue(defaultValue)
      updateField(path, fieldKey, localKey, defaultValue, newType)
    }

    const addNestedField = () => {
      const newData = { ...data }
      const keys = path ? path.split('.') : []
      let current = newData
      for (const k of keys) {
        current = current[k]
      }
      if (!current[localKey]) {
        current[localKey] = {}
      }
      const newKey = `new_field_${Date.now()}`
      current[localKey][newKey] = ''
      updateData(newData)
    }

    const addArrayItem = () => {
      const newData = { ...data }
      const keys = path ? path.split('.') : []
      let current = newData
      for (const k of keys) {
        current = current[k]
      }
      if (!Array.isArray(current[localKey])) {
        current[localKey] = []
      }
      current[localKey].push('')
      updateData(newData)
    }

    return (
      <div className={`border border-gray-200 rounded-lg p-3 mb-2 ${level > 0 ? 'ml-6 bg-gray-50' : 'bg-white'}`}>
        <div className="flex items-center gap-2 mb-2">
          {isObject && (
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-gray-500 hover:text-gray-700"
            >
              {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </button>
          )}
          
          <input
            type="text"
            value={localKey}
            onChange={(e) => {
              const newKey = e.target.value
              handleKeyChange(newKey)
            }}
            onBlur={() => {
              // Flush any pending updates on blur
              if (updateTimerRef.current) {
                clearTimeout(updateTimerRef.current)
                isUpdatingRef.current = true
                updateField(path, fieldKey, keyRef.current, valueRef.current, valueType)
              }
            }}
            placeholder="Field name"
            className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          
          <select
            value={valueType}
            onChange={(e) => handleTypeChange(e.target.value)}
            className="px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="string">Text</option>
            <option value="number">Number</option>
            <option value="boolean">True/False</option>
            <option value="array">List</option>
            <option value="object">Object</option>
          </select>
          
          <button
            type="button"
            onClick={() => deleteField(path, fieldKey)}
            className="text-red-500 hover:text-red-700 p-1"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        {valueType === 'object' && isObject ? (
          <div>
            {isExpanded && (
              <div className="mt-2 space-y-2">
                {Object.entries(fieldValue).map(([key, val], index) => (
                  <FieldEditor
                    key={`${fieldId || fieldKey}-nested-${index}-${key}`}
                    fieldId={`${fieldId || fieldKey}-nested-${index}`}
                    fieldKey={key}
                    fieldValue={val}
                    path={path ? `${path}.${localKey}` : localKey}
                    level={level + 1}
                  />
                ))}
                <button
                  type="button"
                  onClick={addNestedField}
                  className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 px-2 py-1"
                >
                  <Plus className="w-3 h-3" />
                  Add Field
                </button>
              </div>
            )}
          </div>
        ) : valueType === 'array' && isArray ? (
          <div className="mt-2 space-y-2">
            {fieldValue.map((item, index) => (
              <div key={index} className="flex items-center gap-2">
                <span className="text-gray-500 text-sm w-6">{index + 1}.</span>
                <input
                  type="text"
                  value={String(item)}
                  onChange={(e) => {
                    const newValue = e.target.value
                    // Update local state immediately
                    const newData = { ...data }
                    const keys = path ? path.split('.') : []
                    let current = newData
                    for (const k of keys) {
                      current = current[k]
                    }
                    current[localKey][index] = newValue
                    // Debounced update
                    updateData(newData)
                  }}
                  className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                />
                <button
                  type="button"
                  onClick={() => {
                    const newData = { ...data }
                    const keys = path ? path.split('.') : []
                    let current = newData
                    for (const k of keys) {
                      current = current[k]
                    }
                    current[localKey].splice(index, 1)
                    updateData(newData)
                  }}
                  className="text-red-500 hover:text-red-700 p-1"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={addArrayItem}
              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 px-2 py-1"
            >
              <Plus className="w-3 h-3" />
              Add Item
            </button>
          </div>
        ) : (
          <input
            type={valueType === 'number' ? 'number' : valueType === 'boolean' ? 'text' : 'text'}
            value={localValue}
            onChange={(e) => {
              const newValue = e.target.value
              handleValueChange(newValue)
            }}
            onBlur={() => {
              // Flush any pending updates on blur
              if (updateTimerRef.current) {
                clearTimeout(updateTimerRef.current)
                isUpdatingRef.current = true
                updateField(path, fieldKey, keyRef.current, valueRef.current, valueType)
              }
            }}
            placeholder={valueType === 'array' ? 'Enter items separated by commas or JSON array' : `Enter ${valueType}`}
            className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        )}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Form Content</h3>
        <button
          type="button"
          onClick={() => addField()}
          className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 px-2 py-1"
        >
          <Plus className="w-4 h-4" />
          Add Field
        </button>
      </div>
      
      <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-lg p-3 bg-gray-50">
        {Object.keys(data).length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="text-sm">No fields added yet. Click "Add Field" to get started.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {Object.entries(data).map(([key, value], index) => (
              <FieldEditor
                key={`field-${index}-${key}`}
                fieldId={`field-${index}`}
                fieldKey={key}
                fieldValue={value}
                path=""
                level={0}
              />
            ))}
          </div>
        )}
      </div>
      
      <div className="text-xs text-gray-500">
        <p>💡 Tip: Use "Object" type to create nested structures, "List" type for arrays</p>
      </div>
    </div>
  )
}

export default FormBuilder

