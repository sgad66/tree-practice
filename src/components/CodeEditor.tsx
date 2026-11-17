import CodeMirror from '@uiw/react-codemirror'
import { cpp } from '@codemirror/lang-cpp'
import { oneDark } from '@codemirror/theme-one-dark'

interface Props {
  value: string
  onChange: (value: string) => void
}

export function CodeEditor({ value, onChange }: Props) {
  return (
    <div className="cm-wrapper">
      <CodeMirror
        value={value}
        height="100%"
        theme={oneDark}
        extensions={[cpp()]}
        onChange={onChange}
        basicSetup={{
          lineNumbers: true,
          foldGutter: true,
          highlightActiveLine: true,
        }}
      />
    </div>
  )
}
