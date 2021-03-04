def ask_user_bool(mess):
    """Envoie à l'utilisateur le message donné, attend à une réponse "oui" ou "non" et la renvoie sous forme de bool"""
    res = None
    possible_ans = {"oui": True, "non": False}
    while res is None:
        possible_ans_str = "/".join(possible_ans.keys())
        input_res = input(f"{mess} {possible_ans_str} ? ").strip().lower()
        try:
            res = possible_ans[input_res]
        except KeyError:
            print(f"Erreur: entrez {possible_ans_str}")
    return res