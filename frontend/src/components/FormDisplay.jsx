import React from 'react'
import { ChevronDown, ChevronRight, FileText, List, Hash } from 'lucide-react'

/**
 * Collapsible section component for nested objects
 */
const CollapsibleSection = ({ title, children, defaultExpanded = false, level = 0 }) => {
  const [isExpanded, setIsExpanded] = React.useState(defaultExpanded)
  const marginLeft = level === 0 ? 'ml-0' : level === 1 ? 'ml-4' : level === 2 ? 'ml-8' : 'ml-12'
  
  return (
    <div className={`${marginLeft} space-y-3`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 mb-2 text-gray-700 hover:text-gray-900 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
        <h3 className="font-semibold text-gray-900 text-lg">
          {title}
        </h3>
      </button>
      {isExpanded && (
        <div className="ml-6 border-l-2 border-gray-200 pl-4">
          {children}
        </div>
      )}
    </div>
  )
}

/**
 * Recursively renders JSON form data in a readable format
 */
const FormDisplay = ({ data, level = 0 }) => {
  if (!data || typeof data !== 'object') {
    return null
  }

  // Handle arrays
  if (Array.isArray(data)) {
    const marginLeft = level === 0 ? 'ml-0' : level === 1 ? 'ml-4' : level === 2 ? 'ml-8' : 'ml-12'
    return (
      <div className={`${marginLeft} space-y-2`}>
        {data.map((item, index) => (
          <div key={index} className="flex items-start gap-2">
            <span className="text-gray-500 font-mono text-sm mt-1 min-w-[24px]">
              {index + 1}.
            </span>
            <div className="flex-1">
              {typeof item === 'object' && item !== null ? (
                <FormDisplay data={item} level={level + 1} />
              ) : (
                <span className="text-gray-700">{String(item)}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Handle objects
  const entries = Object.entries(data)
  
  return (
    <div className="space-y-4">
      {entries.map(([key, value]) => {
        const isCollapsible = typeof value === 'object' && value !== null && !Array.isArray(value)
        
        // Format key to be more readable
        const formattedKey = formatKey(key)
        
        // Handle different value types
        if (value === null || value === undefined) {
          return null
        }

        const marginLeft = level === 0 ? 'ml-0' : level === 1 ? 'ml-4' : level === 2 ? 'ml-8' : 'ml-12'
        
        if (typeof value === 'string') {
          return (
            <div key={key} className={marginLeft}>
              <div className="flex items-start gap-2">
                <span className="font-semibold text-gray-800 min-w-[200px]">
                  {formattedKey}:
                </span>
                <span className="text-gray-700 flex-1">{value}</span>
              </div>
            </div>
          )
        }

        if (typeof value === 'number' || typeof value === 'boolean') {
          return (
            <div key={key} className={marginLeft}>
              <div className="flex items-start gap-2">
                <span className="font-semibold text-gray-800 min-w-[200px]">
                  {formattedKey}:
                </span>
                <span className="text-gray-700">{String(value)}</span>
              </div>
            </div>
          )
        }

        if (Array.isArray(value)) {
          // Special handling for major_sections
          if (key === 'major_sections') {
            return (
              <div key={key} className={`${marginLeft} space-y-3`}>
                <div className="flex items-center gap-2 mb-2">
                  <List className="w-4 h-4 text-blue-600" />
                  <h3 className="font-semibold text-gray-900 text-lg">
                    {formattedKey}
                  </h3>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <ol className="list-decimal list-inside space-y-2">
                    {value.map((item, index) => (
                      <li key={index} className="text-gray-700">
                        {item}
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            )
          }
          
          // Check if array contains strings (simple list) or objects
          const isStringArray = value.length > 0 && typeof value[0] === 'string'
          
          // Special handling for teacher_script and similar script arrays
          const isScriptArray = key === 'teacher_script' || key.includes('script')
          
          return (
            <div key={key} className={`${marginLeft} space-y-3`}>
              <div className="flex items-center gap-2 mb-2">
                <List className="w-4 h-4 text-blue-600" />
                <h3 className="font-semibold text-gray-900 text-lg">
                  {formattedKey}
                </h3>
                <span className="text-sm text-gray-500">
                  ({value.length} {value.length === 1 ? 'item' : 'items'})
                </span>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                {isStringArray ? (
                  isScriptArray ? (
                    <div className="space-y-2 font-mono text-sm">
                      {value.map((item, index) => (
                        <div key={index} className="text-gray-700 pl-4 border-l-2 border-blue-300">
                          {item}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <ul className="list-disc list-inside space-y-2">
                      {value.map((item, index) => (
                        <li key={index} className="text-gray-700">{item}</li>
                      ))}
                    </ul>
                  )
                ) : (
                  <FormDisplay data={value} level={level + 1} />
                )}
              </div>
            </div>
          )
        }

        if (typeof value === 'object' && value !== null) {
          // Special handling for "note" field
          if (key === 'note') {
            return (
              <div key={key} className={`${marginLeft} mb-4`}>
                <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-r-lg p-4">
                  <p className="text-gray-800 italic">
                    <span className="font-semibold">Note: </span>
                    {value}
                  </p>
                </div>
              </div>
            )
          }
          
          // Check if this looks like a section/subsection (has name, purpose, order, etc.)
          const isSection = 'name' in value || 'purpose' in value || 'order' in value || 'label' in value
          const isComponent = 'definition' in value || 'formatting' in value
          
          // Check if this is a dynamic_sections object (like in Form-C)
          const isDynamicSection = key === 'dynamic_sections' || key === 'lesson_structure'
          
          if (isSection) {
            return (
              <div key={key} className={`${marginLeft} mb-6`}>
                <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4 shadow-sm">
                  {value.name && (
                    <h3 className="font-bold text-gray-900 text-lg mb-2">
                      {value.order && `[Section ${value.order}] `}
                      {value.label && `[Section ${value.label}] `}
                      {value.name}
                    </h3>
                  )}
                  {value.purpose && (
                    <div className="mb-3">
                      <span className="font-semibold text-gray-700">Purpose: </span>
                      <span className="text-gray-700">{value.purpose}</span>
                    </div>
                  )}
                  {value.explanation && (
                    <div className="mb-3 bg-white rounded p-3 border border-gray-200">
                      <span className="font-semibold text-gray-700">Explanation: </span>
                      <span className="text-gray-700">{value.explanation}</span>
                    </div>
                  )}
                  {value.example_output && (
                    <div className="mb-3 bg-white rounded p-3 border border-gray-200">
                      <span className="font-semibold text-gray-700">Example Output: </span>
                      <span className="text-gray-700">{value.example_output}</span>
                    </div>
                  )}
                  {value.reference && (
                    <div className="mb-3">
                      <span className="font-semibold text-gray-700">Reference: </span>
                      <span className="text-blue-600 font-medium">{value.reference}</span>
                    </div>
                  )}
                  {/* Render other fields in the section */}
                  {Object.entries(value).map(([subKey, subValue]) => {
                    if (['name', 'purpose', 'order', 'label', 'explanation', 'example_output', 'reference'].includes(subKey)) {
                      return null
                    }
                    return (
                      <div key={subKey} className="mt-2">
                        <FormDisplay data={{ [subKey]: subValue }} level={level + 1} />
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          }
          
          if (isComponent) {
            return (
              <div key={key} className={`${marginLeft} mb-4`}>
                <div className="bg-green-50 border-l-4 border-green-500 rounded-r-lg p-4 shadow-sm">
                  <h4 className="font-semibold text-gray-900 mb-2">
                    [Component] {formattedKey}
                  </h4>
                  {value.definition && (
                    <div className="mb-2">
                      <span className="font-semibold text-gray-700">Definition: </span>
                      <span className="text-gray-700">{value.definition}</span>
                    </div>
                  )}
                  {value.formatting && (
                    <div className="mb-2">
                      <span className="font-semibold text-gray-700">Formatting: </span>
                      <span className="text-gray-700">{value.formatting}</span>
                    </div>
                  )}
                  {value.requirement && (
                    <div className="mb-2">
                      <span className="font-semibold text-gray-700">Requirement: </span>
                      <span className="text-gray-700">{value.requirement}</span>
                    </div>
                  )}
                  {value.reference && (
                    <div className="mb-2">
                      <span className="font-semibold text-gray-700">Reference: </span>
                      <span className="text-blue-600 font-medium">{value.reference}</span>
                    </div>
                  )}
                  {value.adaptation_prompt && (
                    <div className="mb-2">
                      <span className="font-semibold text-gray-700">Adaptation Prompt: </span>
                      <span className="text-gray-700">{value.adaptation_prompt}</span>
                    </div>
                  )}
                  {value.response_to && (
                    <div className="mb-2">
                      <span className="font-semibold text-gray-700">Response To: </span>
                      <span className="text-gray-700">{value.response_to}</span>
                    </div>
                  )}
                  {/* Handle nested objects like levels */}
                  {value.levels && (
                    <div className="mt-2">
                      <span className="font-semibold text-gray-700">Levels:</span>
                      <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
                        {Object.entries(value.levels).map(([levelKey, levelValue]) => (
                          <li key={levelKey} className="text-gray-700">
                            <span className="capitalize font-medium">{levelKey}:</span> {levelValue}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {value.options && Array.isArray(value.options) && (
                    <div className="mt-2">
                      <span className="font-semibold text-gray-700">Options:</span>
                      <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
                        {value.options.map((option, idx) => (
                          <li key={idx} className="text-gray-700">{option}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {/* Render any other fields */}
                  {Object.entries(value).map(([subKey, subValue]) => {
                    if (['definition', 'formatting', 'requirement', 'reference', 'adaptation_prompt', 'response_to', 'levels', 'options'].includes(subKey)) {
                      return null
                    }
                    if (typeof subValue === 'object' && subValue !== null) {
                      return (
                        <div key={subKey} className="mt-2">
                          <FormDisplay data={{ [subKey]: subValue }} level={level + 1} />
                        </div>
                      )
                    }
                    return null
                  })}
                </div>
              </div>
            )
          }

          // Special handling for dynamic_sections and lesson_structure
          if (isDynamicSection) {
            return (
              <div key={key} className={`${marginLeft} space-y-4`}>
                <h3 className="font-semibold text-gray-900 text-xl mb-3">
                  {formattedKey}
                </h3>
                <div className="space-y-4">
                  <FormDisplay data={value} level={level + 1} />
                </div>
              </div>
            )
          }
          
          // Regular nested object
          return (
            <div key={key}>
              {isCollapsible ? (
                <CollapsibleSection 
                  title={formattedKey} 
                  defaultExpanded={level < 2}
                  level={level}
                >
                  <FormDisplay data={value} level={level + 1} />
                </CollapsibleSection>
              ) : (
                <div className={`${marginLeft} space-y-3`}>
                  <h3 className="font-semibold text-gray-900 text-lg mb-2">
                    {formattedKey}
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <FormDisplay data={value} level={level + 1} />
                  </div>
                </div>
              )}
            </div>
          )
        }

        return null
      })}
    </div>
  )
}

/**
 * Formats a key to be more readable
 */
const formatKey = (key) => {
  // Handle form keys (form_a, form_b, etc.)
  if (key.startsWith('form_')) {
    return 'Form Information'
  }
  
  // Convert snake_case to Title Case
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Main component that extracts the form data and displays it
 */
const FormContentDisplay = ({ content }) => {
  if (!content) {
    return (
      <div className="text-center text-gray-500 py-8">
        <FileText className="w-12 h-12 mx-auto mb-2 text-gray-300" />
        <p>No content available</p>
      </div>
    )
  }

  // Find the form key (form_a, form_b, etc.)
  const formKey = Object.keys(content).find(key => key.startsWith('form_'))
  
  if (!formKey) {
    // If no form key found, display the content as-is
    return (
      <div className="space-y-4">
        <FormDisplay data={content} />
      </div>
    )
  }

  const formData = content[formKey]

  // Extract title and structure_overview if they exist
  const title = formData?.title
  const structureOverview = formData?.structure_overview
  const description = formData?.description

  // Create data without title and structure_overview for recursive display
  const remainingData = { ...formData }
  delete remainingData.title
  delete remainingData.structure_overview
  delete remainingData.description

  return (
    <div className="space-y-6">
      {/* Header Section */}
      {(title || structureOverview || description) && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200 shadow-sm">
          {title && (
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              {title}
            </h2>
          )}
          {structureOverview && (
            <p className="text-gray-700 mb-2">
              <span className="font-semibold">Structure Overview: </span>
              {structureOverview}
            </p>
          )}
          {description && (
            <p className="text-gray-700">
              <span className="font-semibold">Description: </span>
              {description}
            </p>
          )}
        </div>
      )}

      {/* Main Content */}
      <div className="space-y-6">
        <FormDisplay data={remainingData} level={0} />
      </div>
    </div>
  )
}

export default FormContentDisplay

