{
  "@type": "pd_pipeline",
  "stages": [
    # Fill NA values
    {
      "@type": "fill_na",
      "columns": [
        "Age",
        "Fare"
      ],
      "fill_type": "median"
    },
    {
      "@type": "fill_na",
      "columns": [
        "Embarked",
      ],
      "fill_type": "mode",
    },
    {
      "@type": "fill_na",
      "columns": [
        "Cabin",
      ],
      "fill_type": "replace",
      "value": "!"
    },
    # Add Features
    {
      "@type": "add_family_size"
    },
    {
      "@type": "add_is_alone"
    },
    {
      "@type": "add_cabin_category"
    },
    {
      "@type": "add_name_title",
    },
    {
      "@type": "add_deck",
    },
    {
      "@type": "qcut",
      "q": 5,
      "columns": ["Fare"],
      # "result_columns": ["FareBin"],
      "as_str": true,
    },
    {
      "@type": "cut",
      "bins": 10,
      "columns": ["Age"],
      # "result_columns": ["AgeBin"],
      "as_str": true,
    },
    # Filter columns
    {
      "@type": "col_drop",
      "columns": [
        "PassengerId",
        "Cabin",
        "Name",
        "Ticket",
      ]
    },
    # Encode
    {
      "@type": "encode"
    },
    {
      "@type": "one_hot_encode",
      "columns": ["Pclass", "Sex", "Embarked", "NameTitle", "Deck"],
    },
  ]
}
