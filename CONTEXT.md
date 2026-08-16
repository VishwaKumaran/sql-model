# Glossaire du domaine

## Repository

Point d'accès aux données d'un modèle qui fournit les opérations courantes et compose des requêtes sans imposer à l'utilisateur la gestion répétitive de la session.

## Requête composable

Requête construite progressivement par l'ajout de contraintes, de relations, de tri et de pagination, puis exécutée explicitement.

## Filtre composable

Contrainte réutilisable qui peut être combinée avec d'autres contraintes selon une logique `AND` ou `OR`.

## Projection

Sous-ensemble ou forme dérivée des données demandées par le consommateur, plutôt que l'entité complète.

## Pagination

Découpage ordonné d'un résultat en fenêtres successives. La pagination par curseur est privilégiée pour les flux volumineux et évolutifs ; la pagination par offset reste adaptée aux petits ensembles et aux interfaces nécessitant un numéro de page.

## Requête spécialisée

Requête dont les besoins dépassent les primitives déclaratives communes et qui peut utiliser directement les capacités du moteur SQL sous-jacent.

## Builder de requête

Objet qui décrit progressivement une requête sans l'exécuter. Il doit rester inspectable et pouvoir être remis au moteur SQL sous-jacent.

## Query multi-modèle

Requête qui combine plusieurs modèles ou produit une projection qui n'appartient pas à une seule entité. Elle est distincte de l'accès orienté entité fourni par un repository.

## Lecture interactive

Accès synchrone du point de vue de l'utilisateur, optimisé pour une latence prévisible, un nombre limité d'allers-retours et une réponse paginée.

## Traitement bulk/analytique

Opération traitant un volume important de données, optimisée pour le débit, l'utilisation mémoire et le nombre total d'opérations plutôt que pour la latence d'une réponse individuelle.

## Chargement N+1

Dégradation où la lecture d'un ensemble d'entités déclenche une requête supplémentaire par entité pour obtenir des données liées. Une requête composée doit rendre ce coût explicite et évitable.

## Tracking

Suivi d'une entité lue afin que ses changements puissent être synchronisés avec la transaction. Le tracking n'est pas attendu pour une projection ou un flux read-only.

## Flux

Résultat consommé progressivement, avec une mémoire bornée et une durée de vie de connexion explicite. Un flux n'est pas une liste différée implicitement.

## Curseur de pagination

Jeton opaque représentant une position dans un ordre déterministe. Il permet de reprendre une pagination sans dépendre du coût croissant d'un offset.
