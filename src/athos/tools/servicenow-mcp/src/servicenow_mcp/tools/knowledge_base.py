"""
Knowledge lookup tools for the ServiceNow MCP server.

This module provides tools for looking up knowledge articles in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class ListArticlesParams(BaseModel):
    """Parameters for listing knowledge articles."""
    
    limit: int = Field(10, description="Maximum number of articles to return")
    offset: int = Field(0, description="Offset for pagination")
    knowledge_base: Optional[str] = Field(None, description="Filter by knowledge base")
    category: Optional[str] = Field(None, description="Filter by category")
    query: Optional[str] = Field(None, description="Search query for articles")
    workflow_state: Optional[str] = Field(None, description="Filter by workflow state")


class GetArticleParams(BaseModel):
    """Parameters for getting a knowledge article."""

    article_id: str = Field(..., description="ID of the article to get")


def list_articles(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListArticlesParams,
) -> Dict[str, Any]:
    """
    List knowledge articles with filtering options.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for listing articles.

    Returns:
        Dictionary with list of articles and metadata.
    """
    api_url = f"{config.api_url}/table/kb_knowledge"

    # Build query parameters
    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "all",
    }

    # Build query string
    query_parts = []
    if params.knowledge_base:
        query_parts.append(f"kb_knowledge_base.sys_id={params.knowledge_base}")
    if params.category:
        query_parts.append(f"kb_category.sys_id={params.category}")
    if params.workflow_state:
        query_parts.append(f"workflow_state={params.workflow_state}")
    if params.query:
        query_parts.append(f"short_descriptionLIKE{params.query}^ORtextLIKE{params.query}")

    if query_parts:
        query_string = "^".join(query_parts)
        logger.debug(f"Constructed article query string: {query_string}")
        query_params["sysparm_query"] = query_string
    
    # Log the query parameters for debugging
    logger.debug(f"Listing articles with query params: {query_params}")

    # Make request
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        # Get the JSON response
        json_response = response.json()
        logger.debug(f"Article listing raw response: {json_response}")
        
        # Safely extract the result
        if isinstance(json_response, dict) and "result" in json_response:
            result = json_response.get("result", [])
        else:
            logger.error("Unexpected response format: %s", json_response)
            return {
                "success": False,
                "message": f"Unexpected response format",
                "articles": [],
                "count": 0,
                "limit": params.limit,
                "offset": params.offset,
            }

        # Transform the results
        articles = []
        
        # Handle either string or list
        if isinstance(result, list):
            for article_item in result:
                if not isinstance(article_item, dict):
                    logger.warning("Skipping non-dictionary article item: %s", article_item)
                    continue
                    
                # Safely extract values
                article_id = article_item.get("sys_id", "")
                title = article_item.get("short_description", "")
                
                # Extract nested values safely
                knowledge_base = ""
                if isinstance(article_item.get("kb_knowledge_base"), dict):
                    knowledge_base = article_item["kb_knowledge_base"].get("display_value", "")
                
                category = ""
                if isinstance(article_item.get("kb_category"), dict):
                    category = article_item["kb_category"].get("display_value", "")
                
                workflow_state = ""
                if isinstance(article_item.get("workflow_state"), dict):
                    workflow_state = article_item["workflow_state"].get("display_value", "")
                
                created = article_item.get("sys_created_on", "")
                updated = article_item.get("sys_updated_on", "")
                
                articles.append({
                    "id": article_id,
                    "title": title,
                    "knowledge_base": knowledge_base,
                    "category": category,
                    "workflow_state": workflow_state,
                    "created": created,
                    "updated": updated,
                })
        else:
            logger.warning("Result is not a list: %s", result)

        return {
            "success": True,
            "message": f"Found {len(articles)} articles",
            "articles": articles,
            "count": len(articles),
            "limit": params.limit,
            "offset": params.offset,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to list articles: {e}")
        return {
            "success": False,
            "message": f"Failed to list articles: {str(e)}",
            "articles": [],
            "count": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_article(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetArticleParams,
) -> Dict[str, Any]:
    """
    Get a specific knowledge article by ID.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for getting the article.

    Returns:
        Dictionary with article details.
    """
    api_url = f"{config.api_url}/table/kb_knowledge/{params.article_id}"

    # Build query parameters
    query_params = {
        "sysparm_display_value": "true",
    }

    # Make request
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        # Get the JSON response
        json_response = response.json()
        
        # Safely extract the result
        if isinstance(json_response, dict) and "result" in json_response:
            result = json_response.get("result", {})
        else:
            logger.error("Unexpected response format: %s", json_response)
            return {
                "success": False,
                "message": "Unexpected response format",
            }

        if not result or not isinstance(result, dict):
            return {
                "success": False,
                "message": f"Article with ID {params.article_id} not found",
            }

        # Extract values safely
        article_id = result.get("sys_id", "")
        title = result.get("short_description", "")
        text = result.get("text", "")
        
        # Extract nested values safely
        knowledge_base = ""
        if isinstance(result.get("kb_knowledge_base"), dict):
            knowledge_base = result["kb_knowledge_base"].get("display_value", "")
        
        category = ""
        if isinstance(result.get("kb_category"), dict):
            category = result["kb_category"].get("display_value", "")
        
        workflow_state = ""
        if isinstance(result.get("workflow_state"), dict):
            workflow_state = result["workflow_state"].get("display_value", "")
        
        author = ""
        if isinstance(result.get("author"), dict):
            author = result["author"].get("display_value", "")
        
        keywords = result.get("keywords", "")
        article_type = result.get("article_type", "")
        views = result.get("view_count", "0")
        created = result.get("sys_created_on", "")
        updated = result.get("sys_updated_on", "")

        article = {
            "id": article_id,
            "title": title,
            "text": text,
            "knowledge_base": knowledge_base,
            "category": category,
            "workflow_state": workflow_state,
            "created": created,
            "updated": updated,
            "author": author,
            "keywords": keywords,
            "article_type": article_type,
            "views": views,
        }

        return {
            "success": True,
            "message": "Article retrieved successfully",
            "article": article,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to get article: {e}")
        return {
            "success": False,
            "message": f"Failed to get article: {str(e)}",
        } 