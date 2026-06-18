---
type: note
title: Hướng dẫn AI
tags: [ai, claude, reference]
---

# Hướng dẫn AI — nối Claude suy luận trên vault

Mục tiêu: để Claude trả lời "vì sao chọn NSGA-II?", "bật R7/R8 ảnh hưởng gì?",
"đổi đường kính thì patch gì trong file MCOC?"… dựa trên note + liên kết.

## Cách nhanh nhất — plugin Obsidian
1. Settings → Community plugins → cài **Copilot** (hoặc **Smart Connections**).
2. Provider **Anthropic** + dán **API key** (console.anthropic.com).
3. Model: `claude-opus-4-8` (mạnh) hoặc `claude-sonnet-4-6` (rẻ/nhanh).
4. Bật index vault → hỏi đáp RAG trên toàn bộ note (tiếng Việt).
> Không commit API key vào git.

## Cách khác
- Mở repo bằng **Claude Code**: vault là `.md` thuần, Claude đọc trực tiếp;
  wikilink + frontmatter đóng vai đồ thị tri thức.

## Để AI suy luận tốt
- Mỗi note 1 chủ đề; frontmatter `type` + liên kết `[[...]]` rõ nguyên nhân→hệ quả.
- Cập nhật note khi code đổi (để AI không suy luận trên dữ liệu cũ).
- Bắt đầu từ [[Home]] (MOC) để đi theo bản đồ.

## Prompt mẫu
- "Theo [[ADR-001 MCOC là oracle duy nhất]], vì sao cấm xấp xỉ và điều đó ràng buộc engine nào?"
- "Theo [[ADR-005 Bật R7-R8 trong ext không sửa lõi]], R7/R8 được bật bằng cơ chế gì?"
- "Đổi đường kính cọc thì [[Luồng MCOC]] patch những trường nào?"

Liên kết: [[Home]]
