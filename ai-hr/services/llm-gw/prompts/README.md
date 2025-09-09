# LLM Gateway Prompts

This directory contains prompt templates for generating interview scenarios from Job Descriptions using the LLM Gateway service.

## Prompt Templates

### 1. `jd_to_questions_ba.txt`
**Purpose**: Generate interview scenarios for Business Analyst (Anti-fraud) positions

**Usage**: 
- Loaded by `generate_from_jd.py` when `role_type="ba"`
- Creates structured interview questions based on JD content
- Focuses on anti-fraud, requirements engineering, and business analysis skills

**Key Features**:
- 4-6 question categories (AntiFraud_Rules, Requirements_Engineering, etc.)
- L1-L4 question levels with progressive complexity
- Success criteria based on JD keywords
- Logical branching between questions

### 2. `jd_to_questions_it.txt`
**Purpose**: Generate interview scenarios for IT Data Center Operations positions

**Usage**:
- Loaded by `generate_from_jd.py` when `role_type="it"`
- Creates structured interview questions based on JD content
- Focuses on server hardware, networking, and data center operations

**Key Features**:
- 4-6 question categories (DC_HW_x86_RAID_BMC, LAN_SAN_Networking, etc.)
- L1-L4 question levels with technical depth
- Success criteria based on technical terms
- Equivalence branching for related skills

### 3. `rationale_weights.txt`
**Purpose**: Explain the weight calculation formula for interview questions

**Usage**:
- Reference document for understanding question importance
- Used by LLM to assign appropriate weights to questions
- Based on criticality, replaceability, market scarcity, and synergy

**Formula**:
```
weight = (criticality × 0.4) + (replaceability × 0.3) + (market_scarcity × 0.2) + (synergy × 0.1)
```

## Usage Examples

### Generate BA Scenario
```bash
python services/api/scenario/generate_from_jd.py \
  samples/ba_jd.txt \
  ba \
  -o ba_anti_fraud_generated.json
```

### Generate IT Scenario
```bash
python services/api/scenario/generate_from_jd.py \
  samples/it_jd.txt \
  it \
  -o it_dc_ops_generated.json
```

### Test Generation
```bash
python services/api/scenario/test_generation.py
```

## Prompt Structure

Each prompt template follows this structure:

1. **Role Definition**: Defines the expert persona (Senior BA/IT Admin)
2. **Context**: Explains the task and interview scenario creation
3. **JSON Schema**: Provides the exact structure for the output
4. **Categories**: Lists the question categories for the role
5. **Levels**: Explains L1-L4 question complexity levels
6. **Success Criteria**: Guidelines for creating measurable criteria
7. **Branching Logic**: Rules for question flow and transitions
8. **Examples**: Sample questions for each level
9. **Instructions**: Step-by-step generation process

## Customization

### Adding New Role Types
1. Create a new prompt template: `jd_to_questions_[role].txt`
2. Follow the existing structure and adapt categories/levels
3. Update `generate_from_jd.py` to support the new role type
4. Test with sample JD files

### Modifying Existing Prompts
1. Edit the prompt template file
2. Update categories, levels, or examples as needed
3. Test with existing JD files
4. Validate generated scenarios

### Weight Formula Customization
1. Edit `rationale_weights.txt` to modify the formula
2. Adjust component weights (criticality, replaceability, etc.)
3. Update examples and recommendations
4. Test with different JD types

## Best Practices

### Prompt Design
- **Be Specific**: Use concrete examples and clear instructions
- **Provide Structure**: Give exact JSON schema and field requirements
- **Include Examples**: Show expected output format and quality
- **Set Context**: Define the expert persona and task clearly

### Question Generation
- **Progressive Complexity**: L1→L2→L3→L4 with increasing difficulty
- **Measurable Criteria**: Use specific keywords from JD
- **Logical Branching**: Create sensible question flow
- **Role Relevance**: Ensure all questions relate to the position

### Validation
- **Structure Check**: Validate JSON schema compliance
- **Content Quality**: Review generated questions for relevance
- **Weight Distribution**: Ensure appropriate weight distribution
- **Branching Logic**: Verify question flow makes sense

## Troubleshooting

### Common Issues
1. **Invalid JSON**: Check prompt template for syntax errors
2. **Missing Fields**: Ensure all required fields are specified
3. **Poor Quality**: Review prompt examples and instructions
4. **Wrong Categories**: Verify categories match the role type

### Debug Steps
1. Check LLM Gateway service is running
2. Validate prompt template syntax
3. Test with simple JD content
4. Review generated output manually
5. Adjust prompt template as needed

## Integration

### With LLM Gateway
- Prompts are loaded by `generate_from_jd.py`
- Sent to LLM Gateway via `/generate` endpoint
- Response parsed and validated
- Output saved as JSON scenario

### With Scenario System
- Generated scenarios follow the same schema as manual ones
- Compatible with existing scenario loading and execution
- Can be used in interview simulations
- Support all existing features (branching, scoring, etc.)

## Future Enhancements

### Planned Features
- **Multi-language Support**: Prompts in different languages
- **Industry-specific**: Prompts for different industries
- **Custom Categories**: User-defined question categories
- **Template Variables**: Dynamic prompt customization

### Potential Improvements
- **Quality Scoring**: Automatic quality assessment
- **A/B Testing**: Compare different prompt versions
- **Feedback Loop**: Learn from successful interviews
- **Automated Validation**: Enhanced scenario validation
