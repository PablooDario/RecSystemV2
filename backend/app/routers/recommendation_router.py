from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.recommendations.engine import RecommendationEngine
from app.services.recommender_service import RecommendationService
from app.schemas.movie_schema import MovieWithoutActorsResponse, RecommendationResponse, RecommendationSection

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/{user_id}", response_model=RecommendationResponse)
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    engine = RecommendationEngine(db)

    try:
        result = engine.recommend(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Model artifact not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

    if not result["sections"]:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron recomendaciones para el usuario {user_id}."
        )

    return result


@router.get("/content/{user_id}", response_model=list[MovieWithoutActorsResponse])
def get_content_recommendations(user_id: int, db: Session = Depends(get_db)):
    service = RecommendationService(db)

    try:
        recommendations = service.get_content_recommendations(user_id=user_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Model artifact not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

    if recommendations is None:
        raise HTTPException(
            status_code=404,
            detail=f"No positive ratings found for user {user_id}. Cannot generate recommendations."
        )

    return recommendations
