from langgraph.graph import END, StateGraph

from app.graph.dependencies import GraphDependencies
from app.graph.nodes.action_request import ActionRequestNode
from app.graph.nodes.classify_intent import ClassifyIntentNode
from app.graph.nodes.human_escalation import HumanEscalationNode
from app.graph.nodes.ingest_query import IngestQueryNode
from app.graph.nodes.kb_answer import KnowledgeBaseAnswerNode
from app.graph.nodes.response import ResponseNode
from app.graph.router import GraphRouter
from app.graph.state import ChatState


def build_graph(dependencies: GraphDependencies | None = None):
    resolved_dependencies = dependencies or GraphDependencies.default()
    graph = StateGraph(ChatState)

    graph.add_node("ingest_query", IngestQueryNode(resolved_dependencies.history_manager))
    graph.add_node(
        "classify_intent",
        ClassifyIntentNode(resolved_dependencies.intent_classifier),
    )
    graph.add_node(
        "kb_answer",
        KnowledgeBaseAnswerNode(resolved_dependencies.knowledge_base_service),
    )
    graph.add_node(
        "action_request",
        ActionRequestNode(resolved_dependencies.action_request_service),
    )
    graph.add_node(
        "human_escalation",
        HumanEscalationNode(resolved_dependencies.escalation_service),
    )
    graph.add_node("response", ResponseNode(resolved_dependencies.history_manager))

    graph.set_entry_point("ingest_query")
    graph.add_edge("ingest_query", "classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        GraphRouter(resolved_dependencies.intent_router),
        {
            "kb_query": "kb_answer",
            "action_request": "action_request",
            "human_escalation": "human_escalation",
        },
    )
    graph.add_edge("kb_answer", "response")
    graph.add_edge("action_request", "response")
    graph.add_edge("human_escalation", "response")
    graph.add_edge("response", END)

    return graph.compile()
