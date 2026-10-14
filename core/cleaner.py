# -*- coding: utf-8 -*-
"""
WeFeed 微信文章 HTML 清理器
专门剥离微信文章中注入的前端交互垃圾元素（赞赏弹窗、付费弹窗、数字键盘、底部交互条、广告、直播预约浮层、关注二维码等）。
确保 RSS 阅读器（如 Fluent Reader、NetNewsWire、Miniflux）中只保留干净纯粹的文章正文。
"""

from typing import List
from bs4 import BeautifulSoup, Comment

WECHAT_JUNK_SELECTORS: List[str] = [
    # 微信赞赏与付费组件、模态框及键盘
    ".reward_area", "#js_reward_area", ".reward_dialog", ".reward_list",
    ".reward_custom", ".reward_custom-keyboard", ".reward_button", ".icon_reward",
    ".reward_area_primary", ".reward_area_carry_whisper", ".reward_list_dialog",
    ".reward_list_dialog_hd", ".reward_list-loadmore", ".reward-slider-container",
    ".reward-slider", ".reward-input-box", ".reward-input-area", ".reward-input",
    ".reward-input-hint", ".reward-operation-button", ".reward-custorm",
    ".reward_custom-input", ".reward_custom-input_area", ".reward_custom-input_title",
    ".reward_custom-tips", ".reward_custom-keyboard_item", ".reward_custom-keyboard_number",
    ".reward_custom-keyboard_control", ".reward_custom-keyboard_del_btn",
    ".reward_custom-keyboard_submit_btn", ".reward_dialog-error", ".reward_list-wrp",
    ".like_comment_wrp", "#js_reward_wording", "#js_reward_total_frm",
    # 微信移动端底部交互模态框/弹窗
    ".wx_bottom_modal", ".wx_bottom_modal_mask", ".wx_bottom_modal_mask_fixed",
    ".wx_bottom_modal_wrp", ".wx_bottom_modal_group", ".wx_bottom_modal_group_container",
    ".wx_bottom_modal_msg", ".wx_bottom_modal_msg_wrp",
    # 动态加载动画与提示
    ".weui-loadmore", ".weui-loadmore_line", ".weui-loadmore_dot", ".weui-loading",
    # 底部工具栏、点赞在看与Meta元信息
    ".rich_media_tool", ".rich_media_info", "#js_article_bottom_bar",
    "#content_bottom_interaction", ".rich_media_meta_list", ".image_rich_media_meta_list",
    ".show_bottom_border", ".rich_media_meta_area_primary", ".rich_media_meta_area_extra",
    "#js_bottom_share_btn", "#js_bottom_reward_btn", "#js_like_btn", "#js_read_area",
    "#js_article_like", "#js_article_like_area", "#js_share_btn",
    # 广告、赞助商与提示条
    ".wx_bottom_sponsor_ad_area", ".advertisement_container", "#js_sponsor_area",
    ".js_ad_policy_tips", ".policy_tips", ".claim_source_block", ".ad_top_area",
    ".ad_bottom_area", ".rich_media_area_extra", "#js_ad_area",
    # 视频号直播预约卡片
    ".wx_live_area", "#js_live_area", ".channels_card_wrp", "mp-common-videosnap",
    ".finder_live_card", "#js_channels_card",
    # 二维码与公众号关注引导名片
    "#js_pc_qr_code", "#js_pc_weapp_code", "#js_profile_qrcode", ".qr_code_pc_outer",
    ".profile_qrcode", "#js_novel_card",
    # 避免在阅读器中与 Feed 标题重复
    "h1.rich_media_title",
]


def clean_wechat_junk(html_content: str) -> str:
    """清除微信文章中所有前端交互残留垃圾（赞赏弹窗、数字键盘、底部交互条、广告等）"""
    if not html_content or not str(html_content).strip():
        return ""

    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # 1. 移除已知的垃圾组件
        for selector in WECHAT_JUNK_SELECTORS:
            for el in soup.select(selector):
                el.decompose()

        # 2. 移除脚本、样式、外链和注释
        for tag in soup.find_all(["script", "style", "link"]):
            tag.decompose()

        for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
            comment.extract()

        # 3. 移除 aria-hidden="true" 的不可见/模态元素
        for hidden in soup.find_all(attrs={"aria-hidden": "true"}):
            if hidden.name in ("div", "section", "span", "p", "a"):
                hidden.decompose()

        # 4. 移除包含 display:none 样式的非多媒体空或废弃标签
        for hidden in soup.find_all(style=lambda s: s and ("display: none" in s or "display:none" in s)):
            if hidden.name != "img" and not hidden.find(["img", "video", "audio", "iframe"]):
                hidden.decompose()

        # 5. 清理末尾无文本内容的空容器标签
        for empty in soup.find_all(["div", "section", "p"]):
            if empty.name == "div" and empty.get("id") in ("js_image_content", "js_content", "js_article"):
                continue
            if not empty.get_text(strip=True) and not empty.find(["img", "video", "audio", "iframe"]):
                empty.decompose()

        return str(soup).strip()
    except Exception:
        return html_content
