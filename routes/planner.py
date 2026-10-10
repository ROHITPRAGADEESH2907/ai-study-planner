from flask import Blueprint, request, jsonify
from services.planner_service import PlannerService

planner_bp = Blueprint('planner', __name__, url_prefix='/api/plan')

@planner_bp.route('/generate', methods=['POST'])
def generate_plan():
    """
    Generate study schedule from current subjects and topics.
    Optional JSON payload:
        { "start_date": "YYYY-MM-DD" }
    """
    data = request.get_json(silent=True) or {}
    start_date = data.get('start_date')

    response, status_code = PlannerService.generate_plan(start_date=start_date)
    return jsonify(response), status_code

@planner_bp.route('', methods=['GET'])
def get_plan():
    """
    Retrieve generated study sessions.
    Optional Query Parameters:
        ?start_date=YYYY-MM-DD (or ?from=YYYY-MM-DD)
        ?end_date=YYYY-MM-DD   (or ?to=YYYY-MM-DD)
    """
    start_date = request.args.get('start_date') or request.args.get('from')
    end_date = request.args.get('end_date') or request.args.get('to')

    response, status_code = PlannerService.get_plan(start_date=start_date, end_date=end_date)
    return jsonify(response), status_code

@planner_bp.route('/rebalance', methods=['POST'])
def rebalance_plan():
    """
    Recalibrate schedule based on completed topics and remaining time.
    """
    response, status_code = PlannerService.rebalance_plan()
    return jsonify(response), status_code
