import { useRef, useState } from 'react'

export default function UploadArea({ onUpload, disabled = false }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const handleFiles = (files) => {
    const file = files?.[0]
    if (file) onUpload(file)
  }

  return (
    <div
      className={`panel flex min-h-[220px] cursor-pointer flex-col items-center justify-center border-2 border-dashed p-6 text-center transition ${
        dragging ? 'border-amber bg-[#FFF9F0]' : 'border-black/10 hover:border-amber'
      } ${disabled ? 'pointer-events-none opacity-60' : ''}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(event) => {
        event.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault()
        setDragging(false)
        handleFiles(event.dataTransfer.files)
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        onChange={(event) => handleFiles(event.target.files)}
      />
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-lg bg-[#FFF9F0] text-3xl">
        +
      </div>
      <div className="text-base font-semibold text-ink">上传新书</div>
      <div className="mt-2 max-w-[240px] text-sm leading-6 text-muted">
        拖放 PDF 到这里，或点击选择文件
      </div>
    </div>
  )
}

