"""Formatter for converting novel chapters into tech documentation structures."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

# Default section titles by theme for auto-chunking long chapters into doc pages
THEME_SECTION_TITLES: dict[str, list[tuple[str, int]]] = {
    "vue": [
        ("声明响应式状态", 2),
        ("ref() 核心机制", 3),
        ("深层响应性与 DOM 更新", 3),
        ("reactive() 的使用边界", 2),
        ("计算属性与副作用管理", 2),
        ("生命周期钩子调用", 3),
        ("组件间通信与透传 Attributes", 2),
        ("依赖注入 (Provide / Inject)", 3),
        ("性能优化与 KeepAlive 缓存", 2),
        ("自定义指令与底层 DOM 操作", 3),
        ("服务端渲染与水合处理", 2),
        ("TypeScript 类型推导最佳实践", 3),
    ],
    "react": [
        ("Describing the UI and State", 2),
        ("useState() and Re-rendering", 3),
        ("Keeping Components Pure", 3),
        ("Managing State Across Tree", 2),
        ("Extracting State Logic into Reducer", 3),
        ("Passing Data Deeply with Context", 2),
        ("Synchronizing with Effects", 2),
        ("Separating Events from Effects", 3),
        ("Reusing Logic with Custom Hooks", 2),
        ("Optimizing Re-renders with useMemo", 3),
        ("Escape Hatches & useRef", 2),
        ("Concurrent Features & Suspense", 3),
    ],
    "rust": [
        ("Ownership and Memory Safety", 2),
        ("Borrowing and Lifetimes", 3),
        ("Structs and Method Syntax", 2),
        ("Enums and Pattern Matching", 3),
        ("Error Handling with Result<T, E>", 2),
        ("Generic Types, Traits, and Lifetimes", 2),
        ("Writing Automated Tests", 3),
        ("Functional Language Features: Iterators and Closures", 2),
        ("Fearless Concurrency", 2),
        ("Object-Oriented Programming Features", 3),
        ("Advanced Traits and Unsafe Rust", 2),
    ],
    "python": [
        ("Data Model and Execution Flow", 2),
        ("Coroutines and Asynchronous I/O", 3),
        ("Context Managers and Resource Lifecycle", 2),
        ("Type Annotations and Static Checking", 3),
        ("Metaclasses and Class Customization", 2),
        ("Generators and Memory Optimization", 3),
        ("Concurrency with Multiprocessing and Threads", 2),
        ("Standard Library Integrations", 3),
        ("Descriptors and Attribute Access", 2),
        ("Packaging and Module Architecture", 3),
    ],
}

# Snippet generators for realistic code blocks
THEME_CODE_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "vue": [
        {
            "lang": "js",
            "snippet": (
                "import { ref, computed, watchEffect } from 'vue'\n\n"
                "// 响应式状态声明与初始化\n"
                "const count = ref(0)\n"
                "const state = ref({ active: true, step: 'INITIALIZING' })\n\n"
                "const isReady = computed(() => state.value.active && count.value >= 0)\n\n"
                "watchEffect(() => {\n"
                "  if (isReady.value) {\n"
                "    console.debug(`[vue] State synchronized: step=${state.value.step}`)\n"
                "  }\n"
                "})"
            ),
        },
        {
            "lang": "html",
            "snippet": (
                "<script setup>\n"
                "import { ref } from 'vue'\n\n"
                "const message = ref('Vue 3 Documentation')\n"
                "function handleTrigger() {\n"
                "  console.log('Action triggered in reactive context')\n"
                "}\n"
                "</script>\n\n"
                "<template>\n"
                "  <div class=\"doc-container\">\n"
                "    <p>{{ message }}</p>\n"
                "    <button @click=\"handleTrigger\">执行变更</button>\n"
                "  </div>\n"
                "</template>"
            ),
        },
        {
            "lang": "ts",
            "snippet": (
                "import type { Ref } from 'vue'\n\n"
                "interface ContextPayload {\n"
                "  id: string\n"
                "  timestamp: number\n"
                "  payload: Record<string, unknown>\n"
                "}\n\n"
                "export function useRuntimeChannel(id: string): { status: Ref<string> } {\n"
                "  const status = ref('connected')\n"
                "  return { status }\n"
                "}"
            ),
        },
    ],
    "react": [
        {
            "lang": "jsx",
            "snippet": (
                "import { useState, useEffect, useMemo } from 'react';\n\n"
                "export default function SectionView({ id, active }) {\n"
                "  const [status, setStatus] = useState('idle');\n\n"
                "  useEffect(() => {\n"
                "    if (active) {\n"
                "      setStatus('mounted');\n"
                "    }\n"
                "  }, [active]);\n\n"
                "  return (\n"
                "    <section className=\"p-4 rounded-lg bg-surface\">\n"
                "      <h3>State status: {status}</h3>\n"
                "    </section>\n"
                "  );\n"
                "}"
            ),
        },
        {
            "lang": "tsx",
            "snippet": (
                "import React, { createContext, useContext } from 'react';\n\n"
                "interface AppContextType {\n"
                "  theme: 'light' | 'dark';\n"
                "  toggleTheme: () => void;\n"
                "}\n\n"
                "const AppContext = createContext<AppContextType | null>(null);\n\n"
                "export const useAppConfig = () => {\n"
                "  const ctx = useContext(AppContext);\n"
                "  if (!ctx) throw new Error('useAppConfig outside Provider');\n"
                "  return ctx;\n"
                "};"
            ),
        },
    ],
    "rust": [
        {
            "lang": "rust",
            "snippet": (
                "use std::sync::{Arc, Mutex};\n"
                "use std::thread;\n\n"
                "fn main() -> Result<(), Box<dyn std::error::Error>> {\n"
                "    let counter = Arc::new(Mutex::new(0));\n"
                "    let mut handles = vec![];\n\n"
                "    for _ in 0..4 {\n"
                "        let counter = Arc::clone(&counter);\n"
                "        let handle = thread::spawn(move || {\n"
                "            let mut num = counter.lock().unwrap();\n"
                "            *num += 1;\n"
                "        });\n"
                "        handles.push(handle);\n"
                "    }\n"
                "    for h in handles { h.join().unwrap(); }\n"
                "    Ok(())\n"
                "}"
            ),
        },
    ],
    "python": [
        {
            "lang": "python",
            "snippet": (
                "from dataclasses import dataclass\n"
                "import asyncio\n\n"
                "@dataclass\n"
                "class RuntimeContext:\n"
                "    session_id: str\n"
                "    is_active: bool = True\n\n"
                "    async def stream_events(self):\n"
                "        while self.is_active:\n"
                "            await asyncio.sleep(0.5)\n"
                "            yield {'status': 'ok'}"
            ),
        },
    ],
}


@dataclass
class DocBlock:
    type: str  # "paragraph" | "callout" | "code" | "quote"
    content: str = ""
    title: str = ""
    flavor: str = "tip"  # "tip" | "warning" | "info" | "note" | "danger"
    lang: str = ""


@dataclass
class DocSection:
    id: str
    title: str
    level: int  # 2 for H2, 3 for H3
    blocks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DocTocItem:
    id: str
    text: str
    level: int


@dataclass
class DocChapterResponse:
    title: str
    theme: str
    toc: list[dict[str, Any]]
    sections: list[dict[str, Any]]
    paragraph_count: int
    raw_content: str


def _clean_paragraphs(content: str) -> list[str]:
    """Split raw chapter content into non-empty, cleaned paragraphs."""
    raw_paras = re.split(r"\n\s*\n+", content.strip())
    paras: list[str] = []
    for p in raw_paras:
        clean = p.strip()
        if clean:
            # Replace excessive consecutive whitespace inside paragraph
            clean = re.sub(r"[ \t]+", " ", clean)
            paras.append(clean)
    return paras


def _create_callout_title(theme: str, flavor: str, idx: int) -> str:
    """Generate realistic callout title based on theme and flavor."""
    if theme == "vue":
        return "API 参考" if flavor == "info" else ("TIP" if flavor == "tip" else "WARNING")
    elif theme == "react":
        return "Deep Dive" if flavor in ("info", "tip") else "Pitfall"
    elif theme == "rust":
        return "Note" if flavor == "tip" else "Important Memory Safety Rule"
    return "NOTE" if flavor == "tip" else "WARNING"


def format_chapter_as_doc(
    chapter_title: str,
    chapter_content: str,
    theme: str = "vue",
    disguise_mode: str = "hybrid",
) -> DocChapterResponse:
    """Convert novel chapter text into a realistic documentation page structure.

    - theme: 'vue', 'react', 'rust', 'python'
    - disguise_mode: 'clean' (pure doc text), 'hybrid' (callouts + code snippets),
      'code_dense' (frequent code blocks)
    """
    theme_key = theme if theme in THEME_SECTION_TITLES else "vue"
    default_sections = THEME_SECTION_TITLES[theme_key]
    code_templates = THEME_CODE_TEMPLATES.get(theme_key, THEME_CODE_TEMPLATES["vue"])

    paragraphs = _clean_paragraphs(chapter_content)
    if not paragraphs:
        paragraphs = ["暂无正文内容。"]

    # Calculate section division size (usually 3-6 paragraphs per section)
    paras_per_section = max(3, min(6, len(paragraphs) // max(1, min(len(paragraphs), 5))))
    section_chunks: list[list[str]] = []
    for i in range(0, len(paragraphs), paras_per_section):
        section_chunks.append(paragraphs[i : i + paras_per_section])

    sections: list[DocSection] = []
    toc: list[DocTocItem] = []

    code_idx = 0
    for s_idx, chunk in enumerate(section_chunks):
        sec_id = f"section-{s_idx}"
        sec_title, sec_level = default_sections[s_idx % len(default_sections)]
        
        # If this is the first section and chapter title is descriptive, integrate
        if s_idx == 0 and chapter_title and not chapter_title.lower().startswith("chapter"):
            # keep realistic doc header but include TOC
            pass

        toc.append(DocTocItem(id=sec_id, text=sec_title, level=sec_level))

        sec_blocks: list[dict[str, Any]] = []

        # In hybrid/code_dense modes, insert a top callout in the first section
        if s_idx == 0 and disguise_mode in ("hybrid", "code_dense") and chunk:
            callout_flavor = "info" if theme_key == "vue" else "tip"
            callout_title = _create_callout_title(theme_key, callout_flavor, s_idx)
            # Use first paragraph or intro as callout
            first_p = chunk[0]
            sec_blocks.append(
                asdict(
                    DocBlock(
                        type="callout",
                        title=callout_title,
                        flavor=callout_flavor,
                        content=first_p,
                    )
                )
            )
            # remaining paragraphs for this chunk
            body_paras = chunk[1:]
        else:
            body_paras = chunk

        for p_idx, para in enumerate(body_paras):
            sec_blocks.append(asdict(DocBlock(type="paragraph", content=para)))

            # Insert code snippet if hybrid/code_dense
            should_insert_code = False
            if disguise_mode == "code_dense" and p_idx == 0:
                should_insert_code = True
            elif disguise_mode == "hybrid" and (s_idx + p_idx) % 3 == 1 and p_idx == 1:
                should_insert_code = True

            if should_insert_code and code_templates:
                tpl = code_templates[code_idx % len(code_templates)]
                code_idx += 1
                sec_blocks.append(
                    asdict(
                        DocBlock(
                            type="code",
                            lang=tpl.get("lang", "js"),
                            content=tpl.get("snippet", ""),
                        )
                    )
                )

        # In some sections, insert a tip / note callout at the end
        if (
            disguise_mode in ("hybrid", "code_dense")
            and s_idx % 2 == 1
            and len(body_paras) > 2
        ):
            tip_flavor = "tip"
            tip_title = _create_callout_title(theme_key, tip_flavor, s_idx)
            # Take the last paragraph as a tip callout
            last_p = body_paras[-1]
            # Replace the last paragraph block with callout block
            if sec_blocks and sec_blocks[-1]["type"] == "paragraph":
                sec_blocks[-1] = asdict(
                    DocBlock(
                        type="callout",
                        title=tip_title,
                        flavor=tip_flavor,
                        content=last_p,
                    )
                )

        sections.append(
            DocSection(
                id=sec_id,
                title=sec_title,
                level=sec_level,
                blocks=sec_blocks,
            )
        )

    return DocChapterResponse(
        title=chapter_title or "Documentation Overview",
        theme=theme_key,
        toc=[asdict(t) for t in toc],
        sections=[asdict(s) for s in sections],
        paragraph_count=len(paragraphs),
        raw_content=chapter_content,
    )
