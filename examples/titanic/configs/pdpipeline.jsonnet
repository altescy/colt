{
  "@type": "pdp:pd_pipeline",
  "stages": [
    # Fill NA values
    {
      "@type": "pdp:fill_na",
      "columns": [
        "Age",
        "Fare"
      ],
      "fill_type": "median"
    },
    {
      "@type": "pdp:fill_na",
      "columns": [
        "Embarked",
      ],
      "fill_type": "mode",
    },
    {
      "@type": "pdp:fill_na",
      "columns": [
        "Cabin",
      ],
      "fill_type": "replace",
      "value": "!"
    },
    # Add Features
    {
      "@type": "pdp:add_family_size"
    },
    {
      "@type": "pdp:add_is_alone"
    },
    {
      "@type": "pdp:add_cabin_category"
    },
    {
      "@type": "pdp:add_name_title",
    },
    {
      "@type": "pdp:add_deck",
    },
    {
      "@type": "pdp:qcut",
      "q": 5,
      "columns": ["Fare"],
      # "result_columns": ["FareBin"],
      "as_str": true,
    },
    {
      "@type": "pdp:cut",
      "bins": 10,
      "columns": ["Age"],
      # "result_columns": ["AgeBin"],
      "as_str": true,
    },
    # Filter columns
    {
      "@type": "pdp:col_drop",
      "columns": [
        "PassengerId",
        "Cabin",
        "Name",
        "Ticket",
      ]
    },
    # Encode
    {
      "@type": "pdp:encode"
    },
    {
      "@type": "pdp:one_hot_encode",
      "columns": ["Pclass", "Sex", "Embarked", "NameTitle", "Deck"],
    },
  ]
}
