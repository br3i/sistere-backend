from models.database import get_db
from models.feedback import Feedback

def save_feedback(model_name, use_considerations, n_documents, word_list, feedback_type, score, text, query, context, full_response, sources):
    print(f"[save_feedback] model_name {model_name},\n use_considerations {use_considerations},\n n_documents{n_documents},\n word_list {word_list},\n feedback_type {feedback_type},\n score {score},\n text {text},\n query {query},\n context {context},\n full_response {full_response},\n sources {sources}")
    
    db = next(get_db())

    try:
        feedback = Feedback(
            model_name = model_name,
            query=query,
            context=context,
            full_response=full_response,
            sources=sources,
            use_considerations = use_considerations,
            n_documents = n_documents,
            word_list = word_list,
            feedback_type=feedback_type,
            score=score,
            text=text
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)  # Obtener el documento recién creado

        return feedback

    except Exception as e:
        print(f"Error al guardar el feedback o registrar en la base de datos: {e}")
        db.rollback() 
        return None
    finally:
        db.close()