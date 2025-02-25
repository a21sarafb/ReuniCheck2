# /modules/questions.py
def main():
    while True:
        print("\n¿Qué deseas hacer?")
        print("1. Añadir usuarios (participants)")
        print("2. Ingresar un tema y generar preguntas")
        print("3. Salir")
        opcion = input("Selecciona una opción [1/2/3]: ")

        if opcion == '1':
            from user_generator import main as user_main
            user_main()
        elif opcion == '2':
            from question_generator import QuestionGenerator
            generator = QuestionGenerator()
            generator.create_questions()
        elif opcion == '3':
            print("Saliendo del programa.")
            break
        else:
            print("Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    main()
