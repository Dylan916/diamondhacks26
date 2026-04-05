import { useState } from 'react'

export default function UrlInputList({ externalUrls, setExternalUrls }) {
  const handleChange = (index, value) => {
    const newUrls = [...externalUrls]
    newUrls[index] = value
    setExternalUrls(newUrls)
  }

  const handleAdd = () => {
    setExternalUrls([...externalUrls, ''])
  }

  const handleRemove = (index) => {
    if (externalUrls.length === 1) return // Keep at least one
    const newUrls = [...externalUrls]
    newUrls.splice(index, 1)
    setExternalUrls(newUrls)
  }

  return (
    <div className="url-input-list">
      <h3 className="text-xl font-bold mb-4">Course Websites</h3>
      <p className="mb-4 text-gray-400">
        Paste syllabus pages, professor websites, or course portals here. 
        Canvas is pulled automatically using your Chrome profile.
      </p>
      
      <div className="space-y-3 mb-4">
        {externalUrls.map((url, index) => (
          <div key={index} className="flex gap-2 items-center">
            <input
              type="url"
              className="flex-1 bg-(--elevated) border border-(--border) rounded-lg p-3 text-(--foreground) focus:outline-none focus:ring-2 focus:ring-(--primary)"
              placeholder="https://professor-site.com/cs101"
              value={url}
              onChange={(e) => handleChange(index, e.target.value)}
            />
            {externalUrls.length > 1 && (
              <button
                className="p-3 text-red-500 hover:bg-red-500/10 rounded-lg transition-colors cursor-pointer"
                onClick={() => handleRemove(index)}
                title="Remove site"
              >
                ✕
              </button>
            )}
          </div>
        ))}
      </div>
      
      <button
        onClick={handleAdd}
        className="text-(--primary) font-medium text-sm hover:underline cursor-pointer"
      >
        + Add another site
      </button>
    </div>
  )
}
