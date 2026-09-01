"""Authentic documentation content for emergency Web Boss Mode / Panic Mode."""

from __future__ import annotations

REAL_DOCS: dict[str, dict] = {
    "vue": {
        "title": "响应式基础",
        "theme": "vue",
        "doc_source": "https://cn.vuejs.org/guide/essentials/reactivity-fundamentals.html",
        "toc": [
            {"id": "declaring-reactive-state", "text": "声明响应式状态", "level": 2},
            {"id": "ref", "text": "ref()", "level": 3},
            {"id": "script-setup", "text": "<script setup>", "level": 3},
            {"id": "why-refs", "text": "为什么要使用 ref?", "level": 3},
            {"id": "deep-reactivity", "text": "深层响应性", "level": 3},
            {"id": "dom-update-timing", "text": "DOM 更新时机", "level": 3},
            {"id": "reactive", "text": "reactive()", "level": 2},
            {"id": "reactive-proxy-vs-original", "text": "Reactive Proxy vs. Original", "level": 3},
            {"id": "reactive-limitations", "text": "reactive() 的局限性", "level": 3},
        ],
        "sections": [
            {
                "id": "declaring-reactive-state",
                "title": "声明响应式状态",
                "level": 2,
                "blocks": [
                    {
                        "type": "callout",
                        "flavor": "info",
                        "title": "API 参考",
                        "content": "本页和后面很多页面中都分别包含了选项式 API 和组合式 API 的示例代码。现在你选择的是 组合式 API。你可以使用左侧侧边栏顶部的“API 风格偏好”开关在 API 风格之间切换。",
                    },
                    {
                        "type": "paragraph",
                        "content": "在组合式 API 中，推荐使用 ref() 函数来声明响应式状态：",
                    },
                    {
                        "type": "code",
                        "lang": "js",
                        "content": "import { ref } from 'vue'\n\nconst count = ref(0)",
                    },
                    {
                        "type": "paragraph",
                        "content": "ref() 接收参数，并将其包裹在一个带有 .value 属性的 ref 对象中返回：",
                    },
                    {
                        "type": "code",
                        "lang": "js",
                        "content": "const count = ref(0)\n\nconsole.log(count) // { value: 0 }\nconsole.log(count.value) // 0\n\ncount.value++\nconsole.log(count.value) // 1",
                    },
                ],
            },
            {
                "id": "script-setup",
                "title": "<script setup>",
                "level": 3,
                "blocks": [
                    {
                        "type": "paragraph",
                        "content": "在 setup() 函数中手动暴露大量的状态和方法非常繁琐。幸运的是，我们可以通过使用单文件组件 (SFC) 来避免这种情况。我们可以使用 <script setup> 来大幅度简化代码：",
                    },
                    {
                        "type": "code",
                        "lang": "html",
                        "content": "<script setup>\nimport { ref } from 'vue'\n\nconst count = ref(0)\n\nfunction increment() {\n  count.value++\n}\n</script>\n\n<template>\n  <button @click=\"increment\">\n    {{ count }}\n  </button>\n</template>",
                    },
                    {
                        "type": "paragraph",
                        "content": "<script setup> 中的代码会在每次组件实例被创建的时候执行。任何在 <script setup> 声明的顶层的绑定 (包括变量，函数声明，以及 import 导入的内容) 都能在模板中直接使用。",
                    },
                ],
            },
            {
                "id": "deep-reactivity",
                "title": "深层响应性",
                "level": 3,
                "blocks": [
                    {
                        "type": "paragraph",
                        "content": "Ref 可以持有任何类型的值，包括深层嵌套的对象、数组或者 JavaScript 内置的数据结构，比如 Map。",
                    },
                    {
                        "type": "code",
                        "lang": "js",
                        "content": "import { ref } from 'vue'\n\nconst obj = ref({\n  nested: { count: 0 },\n  arr: ['foo', 'bar']\n})\n\nfunction mutateDeeply() {\n  // 以下都会按照期望工作\n  obj.value.nested.count++\n  obj.value.arr.push('baz')\n}",
                    },
                ],
            },
            {
                "id": "reactive",
                "title": "reactive()",
                "level": 2,
                "blocks": [
                    {
                        "type": "paragraph",
                        "content": "还有另一种声明响应式状态的方式，即使用 reactive() API。与将内部值包装在特殊对象中的 ref 不同，reactive() 将使对象本身具有响应性：",
                    },
                    {
                        "type": "code",
                        "lang": "js",
                        "content": "import { reactive } from 'vue'\n\nconst state = reactive({ count: 0 })\n\n// 在模板中使用：\n// <button @click=\"state.count++\">{{ state.count }}</button>",
                    },
                    {
                        "type": "callout",
                        "flavor": "warning",
                        "title": "reactive() 的局限性",
                        "content": "reactive() API 有两条限制：1. 仅对对象类型有效（对象、数组和 Map、Set 之类的集合类型），而对 string、number 和 boolean 这样的原始类型无效。2. 不能随意地“替换”一个响应式对象，因为这将导致对初始引用的响应性连接丢失。",
                    },
                ],
            },
        ],
    },
    "react": {
        "title": "Quick Start",
        "theme": "react",
        "doc_source": "https://react.dev/learn",
        "toc": [
            {"id": "creating-and-nesting-components", "text": "Creating and nesting components", "level": 2},
            {"id": "writing-markup-with-jsx", "text": "Writing markup with JSX", "level": 2},
            {"id": "adding-styles", "text": "Adding styles", "level": 2},
            {"id": "displaying-data", "text": "Displaying data", "level": 2},
            {"id": "rendering-lists", "text": "Rendering lists", "level": 2},
            {"id": "responding-to-events", "text": "Responding to events", "level": 2},
            {"id": "updating-the-screen", "text": "Updating the screen", "level": 2},
            {"id": "using-hooks", "text": "Using Hooks", "level": 3},
        ],
        "sections": [
            {
                "id": "creating-and-nesting-components",
                "title": "Creating and nesting components",
                "level": 2,
                "blocks": [
                    {
                        "type": "paragraph",
                        "content": "React apps are made out of components. A component is a piece of the UI (user interface) that has its own logic and appearance. A component can be as small as a button, or as large as an entire page.",
                    },
                    {
                        "type": "code",
                        "lang": "jsx",
                        "content": "function MyButton() {\n  return (\n    <button>\n      I'm a button\n    </button>\n  );\n}\n\nexport default function MyApp() {\n  return (\n    <div>\n      <h1>Welcome to my app</h1>\n      <MyButton />\n    </div>\n  );\n}",
                    },
                    {
                        "type": "callout",
                        "flavor": "info",
                        "title": "Deep Dive",
                        "content": "Notice that <MyButton /> starts with a capital letter. That's how you know it's a React component. React component names must always start with a capital letter, while HTML tags must be lowercase.",
                    },
                ],
            },
            {
                "id": "updating-the-screen",
                "title": "Updating the screen",
                "level": 2,
                "blocks": [
                    {
                        "type": "paragraph",
                        "content": "Often, you'll want your component to 'remember' some information and display it. For example, maybe you want to count the number of times a button is clicked. To do this, add state to your component.",
                    },
                    {
                        "type": "code",
                        "lang": "jsx",
                        "content": "import { useState } from 'react';\n\nexport default function MyApp() {\n  const [count, setCount] = useState(0);\n\n  function handleClick() {\n    setCount(count + 1);\n  }\n\n  return (\n    <button onClick={handleClick}>\n      Clicked {count} times\n    </button>\n  );\n}",
                    },
                ],
            },
        ],
    },
    "rust": {
        "title": "What is Ownership?",
        "theme": "rust",
        "doc_source": "https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html",
        "toc": [
            {"id": "ownership-rules", "text": "The Ownership Rules", "level": 2},
            {"id": "variable-scope", "text": "Variable Scope", "level": 2},
            {"id": "string-type", "text": "The String Type", "level": 2},
            {"id": "memory-and-allocation", "text": "Memory and Allocation", "level": 2},
        ],
        "sections": [
            {
                "id": "ownership-rules",
                "title": "The Ownership Rules",
                "level": 2,
                "blocks": [
                    {
                        "type": "callout",
                        "flavor": "tip",
                        "title": "Note",
                        "content": "First, let's look at the ownership rules. Keep these rules in mind as we work through the examples that illustrate them:\n1. Each value in Rust has an owner.\n2. There can only be one owner at a time.\n3. When the owner goes out of scope, the value will be dropped.",
                    },
                    {
                        "type": "paragraph",
                        "content": "Ownership is Rust's most unique feature and has deep implications for the rest of the language. It enables Rust to make memory safety guarantees without needing a garbage collector.",
                    },
                    {
                        "type": "code",
                        "lang": "rust",
                        "content": "fn main() {\n    let mut s = String::from(\"hello\");\n    s.push_str(\", world!\"); // push_str() appends a literal to a String\n    println!(\"{s}\"); // This will print `hello, world!`\n}",
                    },
                ],
            },
        ],
    },
    "python": {
        "title": "An Informal Introduction to Python",
        "theme": "python",
        "doc_source": "https://docs.python.org/3/tutorial/introduction.html",
        "toc": [
            {"id": "using-python-as-calculator", "text": "Using Python as a Calculator", "level": 2},
            {"id": "numbers", "text": "Numbers", "level": 3},
            {"id": "strings", "text": "Strings", "level": 3},
            {"id": "lists", "text": "Lists", "level": 3},
        ],
        "sections": [
            {
                "id": "using-python-as-calculator",
                "title": "Using Python as a Calculator",
                "level": 2,
                "blocks": [
                    {
                        "type": "paragraph",
                        "content": "In the following examples, input and output are distinguished by the presence or absence of prompts (>>> and ...): to repeat the example, you must type everything after the prompt, when the prompt appears.",
                    },
                    {
                        "type": "code",
                        "lang": "python",
                        "content": ">>> 2 + 2\n4\n>>> 50 - 5*6\n20\n>>> (50 - 5*6) / 4\n5.0\n>>> 8 / 5  # division always returns a floating point number\n1.6",
                    },
                ],
            },
        ],
    },
}


def get_real_doc(theme: str) -> dict:
    """Return genuine official documentation content for emergency boss mode."""
    theme_key = theme if theme in REAL_DOCS else "vue"
    return REAL_DOCS[theme_key]
